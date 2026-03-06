---
sidebar_position: 4
---

# rhea-dash

A GPU-rendered agent dashboard built with [egui](https://github.com/emilk/egui) and [wgpu](https://wgpu.rs/). Displays agent status, system metrics, and event streams in a native desktop window.

## Overview

rhea-dash is a native desktop application (not a web service) that provides a visual overview of the Rhea agent system. It uses egui for immediate-mode UI and wgpu for GPU-accelerated rendering.

## Tech Stack

```toml
[dependencies]
eframe = { version = "0.29", features = ["wgpu"] }
egui = "0.29"
egui_extras = { version = "0.29", features = ["image"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = "0.4"
```

## Building

```bash
cd rhea-dash
cargo build --release
./target/release/rhea-dash
```

Requires a GPU-capable environment. On macOS, uses Metal via wgpu. On Linux, uses Vulkan.

## Features

- Agent status display (8 agents from the Chronos Protocol)
- Event stream visualization from 0.log
- System metrics dashboard
- Real-time updates

**Status:** Core structure implemented with egui+wgpu rendering pipeline. Dashboard panels and data feeds are in active development.
