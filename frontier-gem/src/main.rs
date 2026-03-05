use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use chrono::Utc;
use mdns_sd::{ServiceDaemon, ServiceInfo};
use std::fs::{self, OpenOptions, File};
use std::io::{self, Write, BufRead, BufReader, Read};
use std::process::Command;
use std::os::unix::fs::PermissionsExt;
use tokio::sync::broadcast;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use std::path::Path;

mod windows_injector;
use windows_injector::TextInjector;

mod discovery;
use discovery::DiscoveryState;

mod focus;
use focus::get_focused_window;

#[derive(Serialize, Deserialize, Debug, Clone)]
struct Frame {
    prev_hash: String,
    timestamp: i64,
    origin: String,
    payload: serde_json::Value,
    hash: String,
}

impl Frame {
    fn new(prev_hash: String, origin: String, payload: serde_json::Value) -> Self {
        let timestamp = Utc::now().timestamp_millis();
        let mut hasher = Sha256::new();
        hasher.update(prev_hash.as_bytes());
        hasher.update(timestamp.to_string().as_bytes());
        hasher.update(serde_json::to_string(&payload).unwrap().as_bytes());
        let hash = hex::encode(hasher.finalize());

        Frame {
            prev_hash,
            timestamp,
            origin,
            payload,
            hash,
        }
    }
}

fn get_last_hash(path: &str) -> String {
    let file = match File::open(path) {
        Ok(f) => f,
        Err(_) => return "0".to_string(),
    };
    let reader = BufReader::new(file);
    reader.lines().last()
        .and_then(|line| line.ok())
        .and_then(|json| serde_json::from_str::<Frame>(&json).ok())
        .map(|frame| frame.hash)
        .unwrap_or_else(|| "0".to_string())
}

fn append_event(origin: &str, data: serde_json::Value) -> Frame {
    let log_path = "/tmp/0.log";
    let last_hash = get_last_hash(log_path);
    let frame = Frame::new(last_hash, origin.to_string(), data);
    
    if let Ok(mut file) = OpenOptions::new().append(true).create(true).open(log_path) {
        let _ = writeln!(file, "{}", serde_json::to_string(&frame).expect("JSON fail"));
        let _ = fs::set_permissions(log_path, fs::Permissions::from_mode(0o666));
    }
    frame
}

// --- DTN OUTBOX ---
fn buffer_to_outbox(data: &[u8]) {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let outbox_path = format!("{}/.frontier_outbox.jsonl", home);
    if let Ok(mut file) = OpenOptions::new().append(true).create(true).open(&outbox_path) {
        let _ = file.write_all(data);
        let _ = file.write_all(b"\n");
    }
}

async fn drain_outbox() {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let outbox_path = format!("{}/.frontier_outbox.jsonl", home);
    if !Path::new(&outbox_path).exists() { return; }

    if let Ok(file) = File::open(&outbox_path) {
        let reader = BufReader::new(file);
        let mut lines_to_keep = Vec::new();
        for line in reader.lines() {
            if let Ok(content) = line {
                if let Ok(mut stream) = TcpStream::connect("127.0.0.1:4444").await {
                    if stream.write_all(content.as_bytes()).await.is_ok() {
                        let _ = stream.write_all(b"\n").await;
                        continue;
                    }
                }
                lines_to_keep.push(content);
            }
        }
        if lines_to_keep.is_empty() {
            let _ = fs::remove_file(&outbox_path);
        } else {
            let _ = fs::write(&outbox_path, lines_to_keep.join("\n") + "\n");
        }
    }
}

async fn run_http_server(addr: &str, tx: broadcast::Sender<String>) -> io::Result<()> {
    let listener = TcpListener::bind(addr).await?;
    println!("🌐 HTTP Server Online at {}", addr);
    io::stdout().flush().unwrap();

    loop {
        match listener.accept().await {
            Ok((mut socket, _)) => {
                let tx = tx.clone();
                tokio::spawn(async move {
                    let mut buf = vec![0u8; 4096];
                    match socket.read(&mut buf).await {
                        Ok(n) if n > 0 => {
                            let request = String::from_utf8_lossy(&buf[..n]);
                            
                            // Parse HTTP request line
                            let lines: Vec<&str> = request.lines().collect();
                            if lines.is_empty() { return; }
                            
                            let parts: Vec<&str> = lines[0].split_whitespace().collect();
                            let method = parts.get(0).map(|s| *s).unwrap_or("GET");
                            let path = parts.get(1).map(|s| *s).unwrap_or("/");
                            
                            // Extract body from POST requests
                            let body = if method == "POST" {
                                lines.iter().rev().next().unwrap_or(&"{}").to_string()
                            } else {
                                "{}".to_string()
                            };
                            
                            // Build response with CORS headers
                            let cors_origin = "*";  // Or use specific extension ID
                            let response = match method {
                                "OPTIONS" => {
                                    format!(
                                        "HTTP/1.1 200 OK\r\n\
                                         Access-Control-Allow-Origin: {}\r\n\
                                         Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                                         Access-Control-Allow-Headers: Content-Type\r\n\
                                         Content-Length: 0\r\n\
                                         Connection: close\r\n\
                                         \r\n",
                                        cors_origin
                                    )
                                },
                                "POST" | "GET" => {
                                    // Handle different endpoints
                                    if path == "/api/discovery" && method == "GET" {
                                        // AI Discovery endpoint
                                        let mut discovery_state = DiscoveryState::with_example_nodes();
                                        
                                        // Update system focus
                                        if let Ok(focused) = get_focused_window() {
                                            discovery_state.system_info.system_focus = focused.process_name.clone();
                                            discovery_state.system_info.focus_window_class = focused.window_class.clone();
                                            discovery_state.system_info.focus_title = focused.window_title.clone();
                                            discovery_state.system_info.timestamp_focus = Utc::now();
                                        }
                                        
                                        let response_body = discovery_state.to_json()
                                            .unwrap_or_else(|_| "{}".to_string());

                                        let frame = append_event("discovery", serde_json::json!({
                                            "nodes_count": discovery_state.active_nodes.len(),
                                            "focus": discovery_state.system_info.system_focus
                                        }));
                                        let _ = tx.send(serde_json::to_string(&frame).unwrap());

                                        format!(
                                            "HTTP/1.1 200 OK\r\n\
                                             Access-Control-Allow-Origin: {}\r\n\
                                             Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                                             Access-Control-Allow-Headers: Content-Type\r\n\
                                             Content-Type: application/json\r\n\
                                             Content-Length: {}\r\n\
                                             Connection: close\r\n\
                                             \r\n\
                                             {}",
                                            cors_origin,
                                            response_body.len(),
                                            response_body
                                        )
                                    } else if path == "/api/inject" && method == "POST" {
                                        // Text injection endpoint (Windows only)
                                        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&body) {
                                            let text = json.get("text")
                                                .and_then(|v| v.as_str())
                                                .unwrap_or("")
                                                .to_string();
                                            
                                            let delay_ms = json.get("delay_ms")
                                                .and_then(|v| v.as_u64())
                                                .unwrap_or(50) as u32;

                                            // Attempt injection
                                            match TextInjector::inject_text(&text, delay_ms) {
                                                Ok(_) => {
                                                    let response_body = serde_json::json!({
                                                        "status": "ok",
                                                        "message": "Text injected successfully",
                                                        "characters": text.len(),
                                                        "timestamp": Utc::now().timestamp()
                                                    }).to_string();

                                                    let frame = append_event("inject", serde_json::json!({
                                                        "status": "ok",
                                                        "chars": text.len()
                                                    }));
                                                    let _ = tx.send(serde_json::to_string(&frame).unwrap());

                                                    format!(
                                                        "HTTP/1.1 200 OK\r\n\
                                                         Access-Control-Allow-Origin: {}\r\n\
                                                         Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                                                         Access-Control-Allow-Headers: Content-Type\r\n\
                                                         Content-Type: application/json\r\n\
                                                         Content-Length: {}\r\n\
                                                         Connection: close\r\n\
                                                         \r\n\
                                                         {}",
                                                        cors_origin,
                                                        response_body.len(),
                                                        response_body
                                                    )
                                                },
                                                Err(e) => {
                                                    let error_msg = format!("{}", e);
                                                    let response_body = serde_json::json!({
                                                        "status": "error",
                                                        "message": error_msg,
                                                        "timestamp": Utc::now().timestamp()
                                                    }).to_string();

                                                    format!(
                                                        "HTTP/1.1 400 Bad Request\r\n\
                                                         Access-Control-Allow-Origin: {}\r\n\
                                                         Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                                                         Access-Control-Allow-Headers: Content-Type\r\n\
                                                         Content-Type: application/json\r\n\
                                                         Content-Length: {}\r\n\
                                                         Connection: close\r\n\
                                                         \r\n\
                                                         {}",
                                                        cors_origin,
                                                        response_body.len(),
                                                        response_body
                                                    )
                                                }
                                            }
                                        } else {
                                            let response_body = serde_json::json!({
                                                "status": "error",
                                                "message": "Invalid JSON in request body",
                                                "timestamp": Utc::now().timestamp()
                                            }).to_string();

                                            format!(
                                                "HTTP/1.1 400 Bad Request\r\n\
                                                 Access-Control-Allow-Origin: {}\r\n\
                                                 Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                                                 Access-Control-Allow-Headers: Content-Type\r\n\
                                                 Content-Type: application/json\r\n\
                                                 Content-Length: {}\r\n\
                                                 Connection: close\r\n\
                                                 \r\n\
                                                 {}",
                                                cors_origin,
                                                response_body.len(),
                                                response_body
                                            )
                                        }
                                    } else {
                                        // Generic event endpoint
                                        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&body) {
                                            let frame = append_event("http", json);
                                            let _ = tx.send(serde_json::to_string(&frame).unwrap());
                                        }
                                        
                                        let response_body = serde_json::json!({
                                            "status": "ok",
                                            "path": path,
                                            "timestamp": Utc::now().timestamp()
                                        }).to_string();
                                        
                                        format!(
                                            "HTTP/1.1 200 OK\r\n\
                                             Access-Control-Allow-Origin: {}\r\n\
                                             Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                                             Access-Control-Allow-Headers: Content-Type\r\n\
                                             Content-Type: application/json\r\n\
                                             Content-Length: {}\r\n\
                                             Connection: close\r\n\
                                             \r\n\
                                             {}",
                                            cors_origin,
                                            response_body.len(),
                                            response_body
                                        )
                                    }
                                },
                                _ => {
                                    format!(
                                        "HTTP/1.1 405 Method Not Allowed\r\n\
                                         Access-Control-Allow-Origin: {}\r\n\
                                         Content-Length: 0\r\n\
                                         Connection: close\r\n\
                                         \r\n",
                                        cors_origin
                                    )
                                }
                            };
                            
                            let _ = socket.write_all(response.as_bytes()).await;
                        }
                        _ => {}
                    }
                });
            }
            Err(e) => eprintln!("⚠️ HTTP Accept Error: {}", e),
        }
    }
}

async fn run_daemon_bus(tx: broadcast::Sender<String>) -> io::Result<()> {
    let addr = "127.0.0.1:4444";
    let listener = TcpListener::bind(addr).await?;
    println!("🚌 Bus Online at TCP {}", addr);
    io::stdout().flush().unwrap();

    loop {
        match listener.accept().await {
            Ok((socket, _)) => {
                let tx = tx.clone();
                let mut rx = tx.subscribe();

                tokio::spawn(async move {
                    let (mut reader, mut writer) = socket.into_split();
                    let tx_send = tx.clone();

                    let mut read_task = tokio::spawn(async move {
                        let mut buf = vec![0u8; 8192];
                        loop {
                            match reader.read(&mut buf).await {
                                Ok(0) => break,
                                Ok(n) => {
                                    for chunk in buf[..n].split(|&b| b == b'\n') {
                                        if chunk.is_empty() { continue; }
                                        if let Ok(json) = serde_json::from_slice::<serde_json::Value>(chunk) {
                                            let frame = append_event("cl-tcp", json);
                                            let _ = tx_send.send(serde_json::to_string(&frame).unwrap());
                                        }
                                    }
                                }
                                Err(_) => break,
                            }
                        }
                    });

                    let mut write_task = tokio::spawn(async move {
                        loop {
                            match rx.recv().await {
                                Ok(msg) => {
                                    if writer.write_all(msg.as_bytes()).await.is_err() { break; }
                                    if writer.write_all(b"\n").await.is_err() { break; }
                                }
                                Err(_) => break,
                            }
                        }
                    });

                    let _ = tokio::select! {
                        _ = (&mut read_task) => {},
                        _ = (&mut write_task) => {},
                    };
                });
            }
            Err(e) => eprintln!("⚠️ Accept Error: {}", e),
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("proxy");

    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?;

    rt.block_on(async {
        match mode {
            "daemon" => {
                println!("📡 Gem Daemon Starting...");
                let (tx, _) = broadcast::channel::<String>(1024);
                let tx_mdns = tx.clone();
                let tx_http = tx.clone();

                // Start HTTP server on port 3456 with CORS
                tokio::spawn(async move {
                    if let Err(e) = run_http_server("127.0.0.1:3456", tx_http).await {
                        eprintln!("❌ HTTP Server Fatal Error: {}", e);
                    }
                });

                // Start mDNS discovery
                tokio::spawn(async move {
                    if let Ok(mdns) = ServiceDaemon::new() {
                        let service = ServiceInfo::new("_frontier-gem._tcp.local.", "GemNode", "gem.local.", "127.0.0.1", 4444, None).unwrap();
                        let _ = mdns.register(service);
                        if let Ok(browser) = mdns.browse("_frontier-gem._tcp.local.") {
                            while let Ok(event) = browser.recv_async().await {
                                if let mdns_sd::ServiceEvent::ServiceResolved(info) = event {
                                    let msg = serde_json::json!({"type": "discovery", "name": info.get_fullname()});
                                    let _ = tx_mdns.send(serde_json::to_string(&append_event("mdns", msg)).unwrap());
                                }
                            }
                        }
                    }
                });

                if let Err(e) = run_daemon_bus(tx).await {
                    eprintln!("❌ Bus Fatal Error: {}", e);
                }
            },
            "proxy" => {
                drain_outbox().await;
                let mut stdin = io::stdin();
                loop {
                    let mut len_buf = [0u8; 4];
                    if stdin.read_exact(&mut len_buf).is_ok() {
                        let len = u32::from_ne_bytes(len_buf) as usize;
                        let mut buf = vec![0u8; len];
                        if stdin.read_exact(&mut buf).is_ok() {
                            let mut sent = false;
                            if let Ok(mut stream) = TcpStream::connect("127.0.0.1:4444").await {
                                if stream.write_all(&buf).await.is_ok() {
                                    let _ = stream.write_all(b"\n").await;
                                    sent = true;
                                }
                            }
                            if !sent { buffer_to_outbox(&buf); }
                        }
                    } else { break; }
                }
            },
            "install" => {
                let target_path = "/usr/local/bin/frontier-gem";
                let exe_path = std::env::current_exe().unwrap();
                println!("🛠  Installing to {}...", target_path);
                let _ = Command::new("sudo").args(["cp", exe_path.to_str().unwrap(), target_path]).status();
                let _ = Command::new("sudo").args(["codesign", "--force", "-s", "-", target_path]).status();
                println!("✅ Installation complete.");
            },
            _ => {
                // If it's a JSON string, append directly
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(mode) {
                    append_event("cli", json);
                } else {
                    println!("daemon | proxy | install | <json>");
                }
            }
        }
    });

    Ok(())
}
