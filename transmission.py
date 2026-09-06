import json
import os
import glob
from datetime import datetime
import time

OUTBOX_DIR = "outbox"

class TransmissionQueue:
    def __init__(self, outbox_dir=OUTBOX_DIR):
        self.outbox_dir = outbox_dir
        os.makedirs(self.outbox_dir, exist_ok=True)
        # Mock network status
        self.network_available = True
    
    def emit_event(self, event):
        """
        Takes an event dict and queues it for transmission.
        """
        priority = "high" if event.get("event_type") == "incident_hitandrun" else "low"
        
        # Save to local outbox buffer first
        timestamp = int(time.time() * 1000)
        filename = f"{priority}_{timestamp}_{event.get('event_id', 'unknown')}.json"
        filepath = os.path.join(self.outbox_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(event, f, indent=2)
            
        print(f"[EDGE] Event {event.get('event_id')} buffered to outbox as {priority} priority.")
        
        self.flush()
        
    def set_network_status(self, status: bool):
        self.network_available = status
        print(f"\n[NETWORK] Status changed: {'Available' if status else 'Offline'}")
        if status:
            self.flush()

    def flush(self):
        if not self.network_available:
            print("[EDGE] Network offline. Keeping events buffered in outbox.")
            return
            
        # Get all files in outbox
        files = glob.glob(os.path.join(self.outbox_dir, "*.json"))
        if not files:
            return
            
        # Sort files based on filename prefix (high priority first)
        # We named them high_... and low_..., so alphabetically 'high' comes before 'low' 
        files.sort(key=lambda x: os.path.basename(x))
        
        print(f"[TRANSMIT] Flushing {len(files)} events to central dashboard...")
        for filepath in files:
            # Simulate transmission
            with open(filepath, 'r') as f:
                event = json.load(f)
            
            print(f" -> Transmitting {event.get('event_id')} ({event.get('event_type')})...")
            # In real system, this is an HTTP POST to the central dashboard
            
            # On success, remove from outbox
            os.remove(filepath)

if __name__ == "__main__":
    queue = TransmissionQueue()
    
    # Simulate network going offline
    queue.set_network_status(False)
    
    # Emit some events
    queue.emit_event({
        "event_id": "evt_1001",
        "event_type": "pothole",
        "confidence": 0.85
    })
    
    queue.emit_event({
        "event_id": "evt_1002",
        "event_type": "incident_hitandrun",
        "confidence": 0.92
    })
    
    queue.emit_event({
        "event_id": "evt_1003",
        "event_type": "vehicle_count",
        "confidence": 0.99
    })
    
    # Simulate network coming back online
    time.sleep(1)
    queue.set_network_status(True)
