"""
Realistic Fleet Data Generator for SIH 2026 Demo
=================================================
Simulates what actually happens in production:
- 5 buses on overlapping routes through Coimbatore
- Each bus detects the SAME potholes at nearly the same GPS (±3m jitter)
- Each bus detects pedestrians at crossings
- 1-2 hit-and-run incidents captured by nearby buses
- Result: Raw count >> Confirmed count (proves clustering works)
"""
import json
import os
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

# ─── Known problem locations in Coimbatore ───
# These are the "ground truth" issues that multiple buses will detect
KNOWN_POTHOLES = [
    {"lat": 11.0168, "lng": 76.9558, "severity": "large",  "desc": "Deep pothole near Gandhipuram bus stand"},
    {"lat": 11.0185, "lng": 76.9572, "severity": "medium", "desc": "Road damage on Avinashi Road"},
    {"lat": 11.0142, "lng": 76.9535, "severity": "large",  "desc": "Crater near Town Hall junction"},
    {"lat": 11.0201, "lng": 76.9510, "severity": "small",  "desc": "Surface crack on DB Road"},
    {"lat": 11.0125, "lng": 76.9590, "severity": "medium", "desc": "Pothole near RS Puram bus stop"},
]

KNOWN_CROSSINGS = [
    {"lat": 11.0175, "lng": 76.9545, "desc": "Pedestrian crossing at Gandhipuram signal"},
    {"lat": 11.0190, "lng": 76.9565, "desc": "School zone crossing on Cross Cut Road"},
    {"lat": 11.0155, "lng": 76.9520, "desc": "Unmarked crossing near Townhall"},
]

KNOWN_INCIDENTS = [
    {"lat": 11.0188, "lng": 76.9548, "plate": "TN38XY1234", "type": "Hit and Run Offender"},
    {"lat": 11.0160, "lng": 76.9575, "plate": "TN39AB5678", "type": "Rash Driving"},
]

BUSES = ["BUS-7G-01", "BUS-7G-02", "BUS-7G-03", "BUS-7G-04", "BUS-7G-05"]

def jitter(val, meters=3):
    """Add ±N meters of GPS jitter (realistic sensor noise)."""
    return val + random.uniform(-meters, meters) * 0.000009  # ~1m ≈ 0.000009°

def make_event(event_type, lat, lng, bus_id, confidence, data=None):
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": event_type,
        "timestamp": (datetime.utcnow() - timedelta(minutes=random.randint(1, 60))).isoformat() + "Z",
        "gps": {"lat": round(jitter(lat), 6), "lng": round(jitter(lng), 6)},
        "bus_id": bus_id,
        "data": data or {},
        "confidence": round(confidence, 2)
    }

def generate():
    pothole_events = []
    pedestrian_events = []
    vehicle_events = []
    incident_events = []

    # ─── Potholes: Each pothole detected by 3-5 buses ───
    for pot in KNOWN_POTHOLES:
        n_buses = random.randint(3, 5)
        detecting_buses = random.sample(BUSES, n_buses)
        for bus in detecting_buses:
            conf = random.uniform(0.70, 0.95)
            pothole_events.append(make_event(
                "pothole", pot["lat"], pot["lng"], bus, conf,
                {"severity_hint": pot["severity"], "description": pot["desc"]}
            ))

    # ─── Pedestrian crossings: 2-3 buses each ───
    for cross in KNOWN_CROSSINGS:
        n_buses = random.randint(2, 3)
        detecting_buses = random.sample(BUSES, n_buses)
        for bus in detecting_buses:
            conf = random.uniform(0.65, 0.90)
            pedestrian_events.append(make_event(
                "pedestrian_crossing", cross["lat"], cross["lng"], bus, conf,
                {"description": cross["desc"]}
            ))

    # ─── Vehicles: counted by each bus on its route ───
    for bus in BUSES:
        # Each bus counts vehicles at a few points along its route
        for _ in range(random.randint(2, 4)):
            lat = 11.0150 + random.uniform(-0.005, 0.005)
            lng = 76.9540 + random.uniform(-0.005, 0.005)
            vehicle_events.append(make_event(
                "vehicle_count", lat, lng, bus, random.uniform(0.80, 0.98),
                {"vehicle_count": random.randint(8, 35), "description": "Traffic density measurement"}
            ))

    # ─── Incidents: captured by 1-2 nearby buses ───
    for inc in KNOWN_INCIDENTS:
        n_buses = random.randint(1, 2)
        detecting_buses = random.sample(BUSES, n_buses)
        for bus in detecting_buses:
            conf = random.uniform(0.55, 0.92)
            incident_events.append(make_event(
                "incident_hitandrun", inc["lat"], inc["lng"], bus, conf,
                {"plate_number": inc["plate"], "incident_type": inc["type"]}
            ))

    # ─── Save to raw/ ───
    os.makedirs("raw", exist_ok=True)
    
    # Clear old data
    for f in os.listdir("raw"):
        os.remove(os.path.join("raw", f))
    
    def save(filename, data):
        path = os.path.join("raw", filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {len(data):>3} events -> {path}")

    save("pothole_events.json", pothole_events)
    save("pedestrian_events.json", pedestrian_events)
    save("vehicle_events.json", vehicle_events)
    save("incident_events.json", incident_events)

    total = len(pothole_events) + len(pedestrian_events) + len(vehicle_events) + len(incident_events)
    print(f"\n  TOTAL RAW EVENTS: {total}")
    print(f"  (Potholes: {len(pothole_events)}, Pedestrians: {len(pedestrian_events)}, "
          f"Vehicles: {len(vehicle_events)}, Incidents: {len(incident_events)})")
    print(f"\n  Expected after clustering:")
    print(f"    Potholes: {len(KNOWN_POTHOLES)} unique locations (from {len(pothole_events)} reports)")
    print(f"    Crossings: {len(KNOWN_CROSSINGS)} unique locations (from {len(pedestrian_events)} reports)")
    print(f"    Incidents: {len(KNOWN_INCIDENTS)} unique events")

    return total

if __name__ == "__main__":
    print("=" * 60)
    print("  Generating Realistic Fleet Sensor Data")
    print("=" * 60)
    generate()
    print("\n  Now run: python integration_pipeline.py")
    print("=" * 60)
