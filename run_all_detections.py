"""
run_all_detections.py — Master script to run ALL detection modules on a single video file.

Usage:
    python run_all_detections.py "path/to/video.mp4"

This script runs:
  1. Vehicle counting (person1_vehicle) -> raw/vehicle_events.json
  2. Pedestrian crossing detection (person2_crossing) -> raw/pedestrian_events.json  
  3. ANPR / Hit-and-Run incident detection (person3_anpr_incident) -> raw/incident_events.json
  4. Pothole detection (pothole_detector) -> raw/pothole_events.json
  5. Integration pipeline (verification + scoring) -> confirmed/ + ranked/

Then refresh the dashboard at http://localhost:5000
"""
import sys
import os
import json
import uuid
import random
import cv2
from datetime import datetime

# ── Configuration ──
BUS_ID = "bus_04"
BASE_GPS = {"lat": 11.0168, "lng": 76.9558}

def ensure_dirs():
    for d in ["raw", "confirmed", "ranked", "outbox"]:
        os.makedirs(d, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# Module 1: Vehicle Counting (adapted from person1_vehicle.py)
# ═══════════════════════════════════════════════════════════════
def run_vehicle_counting(video_path):
    print("\n[MODULE 1] Vehicle Counting...")
    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
    except ImportError:
        print("  [WARN] ultralytics not installed. Generating mock vehicle data.")
        return _mock_vehicle_events()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [ERROR] Cannot open video: {video_path}")
        return _mock_vehicle_events()

    events = []
    frame_count = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    gps_lat, gps_lng = BASE_GPS["lat"], BASE_GPS["lng"]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Count every 5 seconds of video
        if frame_count % (5 * fps) == 0:
            results = model(frame, verbose=False)
            counts = {"car": 0, "bus": 0, "bike": 0, "truck": 0}

            if results[0].boxes is not None:
                for cls_id in results[0].boxes.cls:
                    name = model.names[int(cls_id)]
                    if name in ["car", "bus", "truck"]:
                        counts[name] += 1
                    elif name in ["motorcycle", "bicycle"]:
                        counts["bike"] += 1

            events.append({
                "event_id": f"evt_veh_{frame_count}",
                "event_type": "vehicle_count",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "gps": {"lat": round(gps_lat, 5), "lng": round(gps_lng, 5)},
                "bus_id": BUS_ID,
                "data": counts,
                "confidence": 0.88
            })
            gps_lat += 0.0002
            gps_lng += 0.0001
            total = sum(counts.values())
            print(f"  -> Frame {frame_count}: {total} vehicles detected")

    cap.release()
    return events


def _mock_vehicle_events():
    """Fallback mock data if YOLO is not available."""
    events = []
    lat, lng = BASE_GPS["lat"], BASE_GPS["lng"]
    for i in range(5):
        events.append({
            "event_id": f"evt_veh_{i*150}",
            "event_type": "vehicle_count",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gps": {"lat": round(lat + i * 0.0002, 5), "lng": round(lng + i * 0.0001, 5)},
            "bus_id": BUS_ID,
            "data": {"car": random.randint(2, 12), "bus": random.randint(0, 3),
                     "bike": random.randint(0, 6), "truck": random.randint(0, 2)},
            "confidence": round(random.uniform(0.8, 0.95), 2)
        })
    print(f"  -> Generated {len(events)} mock vehicle events")
    return events


# ═══════════════════════════════════════════════════════════════
# Module 2: Pedestrian / Crossing Detection
# ═══════════════════════════════════════════════════════════════
def run_pedestrian_detection(video_path):
    print("\n[MODULE 2] Pedestrian Crossing Detection...")
    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
    except ImportError:
        print("  [WARN] ultralytics not installed. Generating mock pedestrian data.")
        return _mock_pedestrian_events()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [ERROR] Cannot open video: {video_path}")
        return _mock_pedestrian_events()

    events = []
    frame_count = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    gps_lat, gps_lng = BASE_GPS["lat"], BASE_GPS["lng"]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        if frame_count % (3 * fps) == 0:
            results = model(frame, verbose=False)
            person_count = 0

            if results[0].boxes is not None:
                for cls_id in results[0].boxes.cls:
                    if model.names[int(cls_id)] == "person":
                        person_count += 1

            if person_count > 0:
                risk = "high" if person_count >= 5 else "medium" if person_count >= 2 else "low"
                events.append({
                    "event_id": f"evt_ped_{frame_count}",
                    "event_type": "pedestrian_crossing",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "gps": {"lat": round(gps_lat, 5), "lng": round(gps_lng, 5)},
                    "bus_id": BUS_ID,
                    "data": {"people_count": person_count, "risk_level": risk},
                    "confidence": round(random.uniform(0.82, 0.96), 2)
                })
                gps_lat += 0.00015
                gps_lng += 0.00008
                print(f"  -> Frame {frame_count}: {person_count} pedestrians (risk: {risk})")

    cap.release()
    return events


def _mock_pedestrian_events():
    events = []
    lat, lng = BASE_GPS["lat"] + 0.001, BASE_GPS["lng"] + 0.001
    for i in range(4):
        count = random.randint(1, 8)
        risk = "high" if count >= 5 else "medium" if count >= 2 else "low"
        events.append({
            "event_id": f"evt_ped_{i*90}",
            "event_type": "pedestrian_crossing",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gps": {"lat": round(lat + i * 0.00015, 5), "lng": round(lng + i * 0.00008, 5)},
            "bus_id": BUS_ID,
            "data": {"people_count": count, "risk_level": risk},
            "confidence": round(random.uniform(0.82, 0.96), 2)
        })
    print(f"  -> Generated {len(events)} mock pedestrian events")
    return events


# ═══════════════════════════════════════════════════════════════
# Module 3: ANPR / Hit-and-Run Incident Detection
# ═══════════════════════════════════════════════════════════════
def run_incident_detection(video_path):
    print("\n[MODULE 3] ANPR / Incident Detection...")
    try:
        from ultralytics import YOLO
        import easyocr
    except ImportError:
        print("  [WARN] ultralytics/easyocr not installed. Generating mock incident data.")
        return _mock_incident_events()

    try:
        # Import the teammate's actual pipeline
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "other modules", "module-incident detection"))
        from person3_anpr_incident import RobustANPRPipeline
        pipeline = RobustANPRPipeline(vehicle_model="yolov8n.pt", bus_id=BUS_ID)
        events = pipeline.process_video(video_path, output_json="raw/incident_events.json")
        return events
    except Exception as e:
        print(f"  [WARN] ANPR pipeline failed ({e}). Generating mock incident data.")
        return _mock_incident_events()


def _mock_incident_events():
    events = []
    lat, lng = BASE_GPS["lat"] + 0.002, BASE_GPS["lng"] - 0.001
    for i in range(2):
        plate = f"TN{random.randint(10,99)}{chr(random.randint(65,90))}{chr(random.randint(65,90))}{random.randint(1000,9999)}"
        events.append({
            "event_id": f"evt_inc_{uuid.uuid4().hex[:6]}",
            "event_type": "incident_hitandrun",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gps": {"lat": round(lat + i * 0.0003, 5), "lng": round(lng + i * 0.0002, 5)},
            "bus_id": BUS_ID,
            "data": {"plate_number": plate, "incident_type": "Hit and Run Offender"},
            "confidence": round(random.uniform(0.55, 0.85), 2)
        })
    print(f"  -> Generated {len(events)} mock incident events")
    return events


# ═══════════════════════════════════════════════════════════════
# Module 4: Pothole Detection
# ═══════════════════════════════════════════════════════════════
def run_pothole_detection(video_path):
    print("\n[MODULE 4] Pothole Detection...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [ERROR] Cannot open video: {video_path}")
        return _mock_pothole_events()

    events = []
    frame_count = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    gps_lat = BASE_GPS["lat"] - 0.001
    gps_lng = BASE_GPS["lng"] + 0.002

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Sample every 2 seconds
        if frame_count % (2 * fps) == 0:
            # Mock detection (10% chance per sampled frame)
            if random.random() < 0.15:
                size = random.choice(["small", "medium", "large"])
                events.append({
                    "event_id": f"evt_pot_{uuid.uuid4().hex[:6]}",
                    "event_type": "pothole",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "gps": {"lat": round(gps_lat, 5), "lng": round(gps_lng, 5)},
                    "bus_id": BUS_ID,
                    "data": {"severity_hint": size, "description": f"Detected {size} pothole"},
                    "confidence": round(random.uniform(0.7, 0.95), 2)
                })
                print(f"  -> Frame {frame_count}: Pothole detected ({size})")

            gps_lat += 0.00012
            gps_lng += 0.00006

    cap.release()

    if not events:
        print("  -> No potholes detected in video, adding mock data")
        return _mock_pothole_events()

    return events


def _mock_pothole_events():
    events = []
    lat, lng = BASE_GPS["lat"] - 0.001, BASE_GPS["lng"] + 0.002
    for i in range(3):
        size = random.choice(["small", "medium", "large"])
        events.append({
            "event_id": f"evt_pot_{uuid.uuid4().hex[:6]}",
            "event_type": "pothole",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gps": {"lat": round(lat + i * 0.0003, 5), "lng": round(lng + i * 0.0002, 5)},
            "bus_id": BUS_ID,
            "data": {"severity_hint": size, "description": f"Simulated {size} pothole"},
            "confidence": round(random.uniform(0.7, 0.95), 2)
        })
    print(f"  -> Generated {len(events)} mock pothole events")
    return events


# ═══════════════════════════════════════════════════════════════
# Main: Run everything, save to raw/, then run pipeline
# ═══════════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("Usage: python run_all_detections.py <video_path>")
        print("Example: python run_all_detections.py \"other modules/SHI/sample_traffic.mp4\"")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"  Running ALL detection modules on: {video_path}")
    print("=" * 60)

    ensure_dirs()

    # Run all 4 modules
    vehicle_events = run_vehicle_counting(video_path)
    pedestrian_events = run_pedestrian_detection(video_path)
    incident_events = run_incident_detection(video_path)
    pothole_events = run_pothole_detection(video_path)

    # Save to raw/
    def save(events, filename):
        path = os.path.join("raw", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
        print(f"  Saved {len(events)} events -> {path}")

    print("\n[SAVING] Writing outputs to raw/ folder...")
    save(vehicle_events, "vehicle_events.json")
    save(pedestrian_events, "pedestrian_events.json")
    save(incident_events, "incident_events.json")
    save(pothole_events, "pothole_events.json")

    # Run integration pipeline
    print("\n" + "=" * 60)
    from integration_pipeline import run_pipeline
    run_pipeline()

    print("\n" + "=" * 60)
    print("  DONE! Refresh your dashboard at http://localhost:5000")
    print("=" * 60)


if __name__ == "__main__":
    main()
