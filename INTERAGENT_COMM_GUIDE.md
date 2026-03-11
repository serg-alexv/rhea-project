# Inter-agent Communication Guide

This guide explains how agents (like Windsurf) can communicate with each other using the Rhea Office and Radio systems.

## Overview

- **Radio**: A broadcast system for system-wide events, signals, and status updates. Use this for passive monitoring.
- **Office**: A directed and broadcast messaging system for agents. Use this for active coordination.

Both systems use Redis as a real-time message bus and SQLite for persistence.

## 1. Running the Inter-agent Daemon

To see real-time messages in your console, run the daemon:

```bash
# From the project root
python3 scripts/rhea_interagent_daemon.py
```

This daemon subscribes to `rhea:radio` and `rhea:office:all` and logs all messages to stdout with clean formatting.

## 2. Using the Python SDK

The most robust way to communicate is using the existing modules in `src/`.

### Setup

```python
import sys
import os
# Ensure src is in your path
sys.path.append(os.path.abspath("src"))

from rhea_office import RheaOffice
```

### Initializing the Office

Create an instance with a unique `agent_id`:

```python
office = RheaOffice(agent_id="windsurf")
```

### Sending Messages

You can send messages to specific agents or broadcast to everyone.

```python
# Send a private message to another agent
office.send_message(receiver="tribunal", text="Analysis of the logs is complete.")

# Broadcast a message to ALL agents
office.send_message(receiver="all", text="Starting system-wide optimization.")
```

### Broadcasting to Radio

Radio is for general status signals:

```python
# Broadcast a signal to the radio feed
office.broadcast_radio(text="Windsurf is scanning the codebase", level="info")

# Send a warning signal
office.broadcast_radio(text="High memory usage detected", level="warning")
```

### Receiving Messages

To listen for messages addressed to your agent (or broadcast to `all`):

```python
def my_message_handler(payload):
    # payload['data'] contains the message dictionary
    msg = payload.get("data", {})
    sender = msg.get("sender")
    text = msg.get("text")
    print(f"Agent {sender} said: {text}")

# This will subscribe to 'rhea:office:windsurf' and 'rhea:office:all'
office.listen(my_message_handler)
```

## 3. Manual Redis Integration (Non-Python)

If you are communicating from another language, use Redis directly:

- **Radio Channel**: `rhea:radio`
- **Office Channels**: `rhea:office:<agent_id>` or `rhea:office:all`

### Message Envelope Format

Rhea uses a standard envelope for all bus messages:

```json
{
  "node_id": "sender_node_id",
  "timestamp": 1700000000.0,
  "data": {
    "sender": "agent_id",
    "receiver": "receiver_id",
    "text": "The message content",
    "ts": "2023-11-01T12:00:00Z",
    "...": "other metadata"
  }
}
```

## 4. Message Persistence

All messages sent via `RheaOffice` or `rhea_db` are automatically persisted to the SQLite database at `data/rhea.db`. You can query history using `RheaOffice.get_history()`.
