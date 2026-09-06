import json
import random
from datetime import datetime, timedelta

def generate_events(n=20):
    event_types = ["pothole", "vehicle_count", "pedestrian_crossing", "incident_hitandrun", "missing_infra"]
    base_lat = 11.0168
    base_lng = 76.9558
    
    events = []
    base_time = datetime.utcnow()
    
    for i in range(n):
        # Generate varied events
        evt_type = random.choices(event_types, weights=[0.4, 0.2, 0.2, 0.05, 0.15])[0]
        
        # Slightly offset GPS (0.0001 deg is ~11 meters)
        lat = base_lat + random.uniform(-0.0001, 0.0001)
        lng = base_lng + random.uniform(-0.0001, 0.0001)
        
        # Create event data
        evt = {
            "event_id": f"evt_{i+1:05d}",
            "event_type": evt_type,
            "timestamp": (base_time - timedelta(minutes=random.randint(0, 60))).isoformat() + "Z",
            "gps": {"lat": round(lat, 5), "lng": round(lng, 5)},
            "bus_id": f"bus_{random.randint(1, 10):02d}",
            "confidence": round(random.uniform(0.6, 0.99), 2)
        }
        
        # Add module-specific data
        if evt_type == "pothole":
            evt["data"] = {"area_px": random.randint(1000, 10000), "severity_hint": random.choice(["low", "medium", "high"])}
        elif evt_type == "vehicle_count":
            evt["data"] = {"count": random.randint(5, 50), "vehicle_types": {"cars": random.randint(2, 20), "bikes": random.randint(1, 15)}}
        elif evt_type == "pedestrian_crossing":
            evt["data"] = {"count": random.randint(1, 10), "risk_level": random.choice(["low", "medium", "high"])}
        elif evt_type == "incident_hitandrun":
            evt["data"] = {"license_plate": f"TN{random.randint(10, 99)}AA{random.randint(1000, 9999)}", "plate_confidence": round(random.uniform(0.5, 0.95), 2)}
        elif evt_type == "missing_infra":
            evt["data"] = {"infra_type": random.choice(["zebra_crossing", "signboard", "road_divider"])}
            
        events.append(evt)
        
    return events

if __name__ == "__main__":
    events = generate_events()
    with open('raw/sample_events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)
    print("Generated raw/sample_events.json")
