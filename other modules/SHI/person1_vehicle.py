import json
from datetime import datetime
import cv2
from ultralytics import YOLO

# Load pretrained YOLO model
model = YOLO("yolov8n.pt")
video_path = "sample_traffic.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
  print(f"ERROR: Could not open video file '{video_path}'.")

events = []
frame_count = 0
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30

print("Starting Vehicle Detection & Counting module...")

while cap.isOpened():
  success, frame = cap.read()
  if not success:
    break

  frame_count += 1
  results = model(frame, verbose=False)

  # Aggregate counts every 30 seconds of video frames
  if frame_count % (30 * fps) == 0:
    counts = {"car": 0, "bus": 0, "bike": 0, "truck": 0}

    if results[0].boxes is not None:
      for cls_id in results[0].boxes.cls:
        class_name = model.names[int(cls_id)]
        if class_name in ["car", "bus", "truck"]:
          counts[class_name] += 1
        elif class_name in ["motorcycle", "bicycle"]:
          counts["bike"] += 1

    event = {
        "event_id": f"evt_veh_{frame_count}",
        "event_type": "vehicle_count",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "gps": {"lat": 11.0168, "lng": 76.9558},
        "bus_id": "bus_04",
        "data": counts,
        "confidence": 0.88,
    }
    events.append(event)
    print(
        f"-> Logged vehicle count at frame {frame_count} (30s interval):"
        f" {counts}"
    )

    # Save live progress to shared JSON file
    with open("vehicle_events.json", "w") as f:
      json.dump(events, f, indent=4)

cap.release()
print(
    "Vehicle Detection & Counting complete. Saved to vehicle_events.json."
)