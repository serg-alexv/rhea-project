import uuid
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict
import rhea_db
from rhea_bus import RheaBus

class RheaOffice:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.bus = RheaBus(node_id=f"office_{agent_id}")

    def send_message(self, receiver: str, text: str, reply_to: Optional[str] = None) -> str:
        """Send a message to another agent or broadcast to 'all'."""
        msg_id = uuid.uuid4().hex[:12]
        msg = {
            "id": msg_id,
            "sender": self.agent_id,
            "receiver": receiver,
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat(),
            "reply_to": reply_to
        }
        
        # 1. Persist to SQLite
        rhea_db.persist_office_message(msg)
        
        # 2. Publish to Redis (persist_office_message already does this, but let's be explicit if needed)
        # Actually persist_office_message in rhea_db.py now handles the bus.publish.
        
        return msg_id

    def listen(self, callback):
        """Listen for messages addressed to this agent."""
        # Subscribe to specific agent channel
        self.bus.subscribe(f"rhea:office:{self.agent_id}", callback)
        # Also subscribe to global broadcast
        self.bus.subscribe("rhea:office:all", callback)

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get message history for this agent."""
        return rhea_db.query_office(limit=limit, agent=self.agent_id)

    def broadcast_radio(self, text: str, level: str = "info", **kwargs):
        """Broadcast a signal to the radio feed."""
        event = {
            "type": "radio",
            "sender": self.agent_id,
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            **kwargs
        }
        rhea_db.persist_radio(event)
