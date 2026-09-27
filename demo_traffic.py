"""
demo_traffic.py - Live Traffic & Vehicle Counting Demo (UNIQUE TRACKING)
Run: python demo_traffic.py "video.mp4"
"""
import sys
import os
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

WINDOW_NAME = "UIS - Traffic Monitoring Module"
BUS_ID = "bus_04"
GPS_LAT, GPS_LNG = 11.0195, 76.9545

VEHICLE_COLORS = {
    "car": (0, 255, 0),
    "bus": (255, 165, 0),
    "truck": (0, 100, 280),
    "motorcycle": (255, 255, 0),
    "bicycle": (255, 0, 280),
}

def run_demo(video_path):
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = 0
    lat, lng = GPS_LAT, GPS_LNG

    # Store unique track IDs for accurate counting
    unique_vehicles = {"car": set(), "bus": set(), "truck": set(), "bike": set()}

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Use model.track() instead of model() to assign unique IDs to vehicles
        results = model.track(frame, persist=True, verbose=False, conf=0.3)

        frame_counts = {"car": 0, "bus": 0, "truck": 0, "bike": 0}

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            class_ids = results[0].boxes.cls.int().cpu().tolist()
            confs = results[0].boxes.conf.cpu().tolist()

            for box, track_id, cls_id, conf in zip(boxes, track_ids, class_ids, confs):
                name = model.names[cls_id]
                x1, y1, x2, y2 = map(int, box)
                
                # Assign to categories and add to unique sets
                if name in ["car", "bus", "truck"]:
                    unique_vehicles[name].add(track_id)
                    frame_counts[name] += 1
                    color = VEHICLE_COLORS.get(name, (0, 255, 0))
                elif name in ["motorcycle", "bicycle"]:
                    unique_vehicles["bike"].add(track_id)
                    frame_counts["bike"] += 1
                    color = VEHICLE_COLORS.get(name, (255, 255, 0))
                else:
                    continue

                # Draw tracking box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{name.upper()} ID:{track_id}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(frame, (x1, y1 - 18), (x1 + label_size[0] + 4, y1), color, -1)
                cv2.putText(frame, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        total_in_frame = sum(frame_counts.values())

        if total_in_frame >= 8:
            congestion = "HEAVY"
            cong_color = (0, 0, 280)
        elif total_in_frame >= 4:
            congestion = "MODERATE"
            cong_color = (0, 165, 280)
        else:
            congestion = "LOW"
            cong_color = (0, 255, 0)

        lat += 0.000005
        lng += 0.000003

        # ── HUD Overlay ──
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 229, 280), 3)
        cv2.putText(frame, "MODULE: TRAFFIC MONITORING (UNIQUE TRACKING)", (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 200), 2)
        cv2.putText(frame, f"Bus: {BUS_ID}", (width - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
        cv2.putText(frame, f"GPS: {lat:.5f}, {lng:.5f}", (width - 250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        # Bottom bar with UNIQUE totals
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, height - 75), (width, height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0)

        y_bottom = height - 15
        cv2.putText(frame, f"Unique Cars: {len(unique_vehicles['car'])}", (15, y_bottom), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.putText(frame, f"Bus: {len(unique_vehicles['bus'])}", (160, y_bottom), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 165, 0), 2)
        cv2.putText(frame, f"Truck: {len(unique_vehicles['truck'])}", (260, y_bottom), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 100, 280), 2)
        cv2.putText(frame, f"Bike: {len(unique_vehicles['bike'])}", (390, y_bottom), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

        cv2.putText(frame, f"Congestion: {congestion}", (width - 300, y_bottom), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cong_color, 2)

        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")

if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "cityRoad_potHoles-side.mp4"
    run_demo(video)
