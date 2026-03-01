//! rhea-health — silent system health daemon
//! Kills zombie processes, tracks CPU hogs, reports to tribunal API.
//! Runs via launchd, logs to ~/.rhea/health.log

use chrono::Utc;
use serde::Serialize;
use signal_hook::consts::{SIGINT, SIGTERM};
use signal_hook::flag;
use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

const SCAN_INTERVAL: Duration = Duration::from_secs(30);
const CPU_KILL_THRESHOLD: f32 = 60.0; // % CPU
const STRIKE_LIMIT: u32 = 3; // consecutive scans above threshold → kill
const API_BASE: &str = "http://localhost:8400";

// Known zombie patterns — processes that should never eat CPU for long
const ZOMBIE_PATTERNS: &[&str] = &[
    "carbonyl",
    "replayd", // Apple screen replay buffer — flag but don't kill
];

// Processes safe to kill when they exceed threshold
const KILLABLE: &[&str] = &["carbonyl"];

#[derive(Debug, Serialize)]
struct HealthEvent {
    ts: String,
    event: String,
    pid: u32,
    name: String,
    cpu: f32,
    action: String,
}

#[derive(Debug, Default)]
struct ProcessTracker {
    strikes: HashMap<u32, (String, u32, f32)>, // pid → (name, strike_count, last_cpu)
}

fn log_dir() -> PathBuf {
    let dir = dirs_home().join(".rhea");
    fs::create_dir_all(&dir).ok();
    dir
}

fn dirs_home() -> PathBuf {
    std::env::var("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/tmp"))
}

fn log_event(event: &HealthEvent) {
    let path = log_dir().join("health.log");
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(&path) {
        let line = serde_json::to_string(event).unwrap_or_default();
        writeln!(f, "{}", line).ok();
    }
}

fn push_to_feed(event: &HealthEvent) {
    let body = serde_json::json!({
        "type": "health",
        "sender": "rhea-health",
        "text": format!("[health] {} pid={} cpu={:.0}% → {}",
            event.event, event.pid, event.cpu, event.action),
    });

    // Fire-and-forget POST to tribunal feed
    let _ = std::process::Command::new("curl")
        .args([
            "-s", "-X", "POST",
            &format!("{}/feed/push", API_BASE),
            "-H", "Content-Type: application/json",
            "-H", "X-API-Key: dev-bypass",
            "-d", &body.to_string(),
            "--connect-timeout", "2",
            "--max-time", "3",
        ])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn();
}

/// Parse `ps aux` output into (pid, cpu%, command_name) tuples
fn scan_processes() -> Vec<(u32, f32, String)> {
    let output = Command::new("ps")
        .args(["aux"])
        .output()
        .ok();

    let output = match output {
        Some(o) => o,
        None => return vec![],
    };

    let text = String::from_utf8_lossy(&output.stdout);
    let mut results = vec![];

    for line in text.lines().skip(1) {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 11 {
            continue;
        }
        let pid: u32 = match parts[1].parse() {
            Ok(p) => p,
            Err(_) => continue,
        };
        let cpu: f32 = match parts[2].parse() {
            Ok(c) => c,
            Err(_) => continue,
        };
        // command is everything from parts[10] onward
        let cmd = parts[10..].join(" ");
        let name = parts[10]
            .rsplit('/')
            .next()
            .unwrap_or(parts[10])
            .to_string();

        if cpu > 5.0 {
            // Only track processes using meaningful CPU
            results.push((pid, cpu, name));
        }
    }

    results
}

fn kill_process(pid: u32) -> bool {
    // SIGTERM first
    let _ = Command::new("kill").arg(pid.to_string()).output();
    thread::sleep(Duration::from_millis(500));

    // Check if still alive, SIGKILL if needed
    let check = Command::new("kill")
        .args(["-0", &pid.to_string()])
        .output();

    if check.map(|o| o.status.success()).unwrap_or(false) {
        let _ = Command::new("kill")
            .args(["-9", &pid.to_string()])
            .output();
    }
    true
}

fn is_killable(name: &str) -> bool {
    KILLABLE.iter().any(|p| name.contains(p))
}

fn is_zombie_pattern(name: &str) -> bool {
    ZOMBIE_PATTERNS.iter().any(|p| name.contains(p))
}

fn run_scan(tracker: &mut ProcessTracker) {
    let procs = scan_processes();
    let mut seen_pids: Vec<u32> = vec![];

    for (pid, cpu, name) in &procs {
        seen_pids.push(*pid);

        if !is_zombie_pattern(name) && *cpu < CPU_KILL_THRESHOLD {
            continue;
        }

        let entry = tracker
            .strikes
            .entry(*pid)
            .or_insert_with(|| (name.clone(), 0, 0.0));
        entry.1 += 1;
        entry.2 = *cpu;

        if entry.1 >= STRIKE_LIMIT && is_killable(name) {
            let event = HealthEvent {
                ts: Utc::now().to_rfc3339(),
                event: "zombie_killed".into(),
                pid: *pid,
                name: name.clone(),
                cpu: *cpu,
                action: "SIGTERM+SIGKILL".into(),
            };
            kill_process(*pid);
            log_event(&event);
            push_to_feed(&event);
            tracker.strikes.remove(pid);
        } else if entry.1 == 1 && *cpu > CPU_KILL_THRESHOLD {
            let event = HealthEvent {
                ts: Utc::now().to_rfc3339(),
                event: "cpu_hog_detected".into(),
                pid: *pid,
                name: name.clone(),
                cpu: *cpu,
                action: format!("tracking (strike {}/{})", entry.1, STRIKE_LIMIT),
            };
            log_event(&event);
        }
    }

    // Clear strikes for processes that are no longer hot
    tracker.strikes.retain(|pid, _| seen_pids.contains(pid));
}

fn write_status(tracker: &ProcessTracker) {
    let path = log_dir().join("health-status.json");
    let status = serde_json::json!({
        "ts": Utc::now().to_rfc3339(),
        "tracking": tracker.strikes.len(),
        "watched": tracker.strikes.iter().map(|(pid, (name, strikes, cpu))| {
            serde_json::json!({
                "pid": pid,
                "name": name,
                "strikes": strikes,
                "cpu": cpu,
            })
        }).collect::<Vec<_>>(),
    });
    fs::write(&path, serde_json::to_string_pretty(&status).unwrap_or_default()).ok();
}

fn main() {
    let running = Arc::new(AtomicBool::new(true));
    flag::register(SIGINT, Arc::clone(&running)).ok();
    flag::register(SIGTERM, Arc::clone(&running)).ok();

    eprintln!(
        "[rhea-health] started at {} — scanning every {}s",
        Utc::now().format("%H:%M:%S"),
        SCAN_INTERVAL.as_secs()
    );

    // Log startup
    let startup = HealthEvent {
        ts: Utc::now().to_rfc3339(),
        event: "daemon_start".into(),
        pid: std::process::id(),
        name: "rhea-health".into(),
        cpu: 0.0,
        action: "monitoring".into(),
    };
    log_event(&startup);

    let mut tracker = ProcessTracker::default();

    while running.load(Ordering::Relaxed) {
        run_scan(&mut tracker);
        write_status(&tracker);

        // Sleep in small increments so we respond to signals
        for _ in 0..(SCAN_INTERVAL.as_secs() * 2) {
            if !running.load(Ordering::Relaxed) {
                break;
            }
            thread::sleep(Duration::from_millis(500));
        }
    }

    eprintln!("[rhea-health] shutting down");
    let shutdown = HealthEvent {
        ts: Utc::now().to_rfc3339(),
        event: "daemon_stop".into(),
        pid: std::process::id(),
        name: "rhea-health".into(),
        cpu: 0.0,
        action: "clean shutdown".into(),
    };
    log_event(&shutdown);
}
