"""
demo_pedestrian.py - Live Pedestrian & Vulnerable Person Detection Demo
Run: python demo_pedestrian.py "other modules/SHI/sample_traffic.mp4"
Press 'q' to quit
"""
import sys
import os
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

WINDOW_NAME = "UIS - Pedestrian Detection Module"
BUS_ID = "bus_04"
GPS_LAT, GPS_LNG = 11.0185, 76.9572

def run_demo(video_path):
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps != fps:
        fps = 30.0
    delay = int(1000 / fps)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = 0
    lat, lng = GPS_LAT, GPS_LNG

    # Use a set to track UNIQUE pedestrian IDs instead of frame-by-frame accumulation
    unique_pedestrians = set()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Use model.track() to assign persistent IDs to objects
        results = model.track(frame, persist=True, verbose=False, conf=0.3)

        person_count = 0
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy
            clss = results[0].boxes.cls
            confs = results[0].boxes.conf
            ids = results[0].boxes.id

            for box, cls_id, conf, obj_id in zip(boxes, clss, confs, ids):
                name = model.names[int(cls_id)]
                x1, y1, x2, y2 = map(int, box)
                confidence = float(conf)
                track_id = int(obj_id)

                if name == "person":
                    person_count += 1
                    unique_pedestrians.add(track_id) # Add to our unique count
                    
                    # Color based on position (simulate risk zones)
                    box_center_y = (y1 + y2) // 2
                    if box_center_y > height * 0.6:  # Close to camera = on road
                        color = (0, 0, 255)  # Red - HIGH RISK
                        risk_tag = "ON ROAD"
                    elif box_center_y > height * 0.4:
                        color = (0, 165, 255)  # Orange - MEDIUM
                        risk_tag = "NEAR ROAD"
                    else:
                        color = (0, 255, 0)  # Green - LOW
                        risk_tag = "SIDEWALK"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    label = f"PERSON {track_id} [{risk_tag}]"
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0] + 5, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                elif name in ["car", "bus", "truck", "motorcycle", "bicycle"]:
                    # Draw vehicles lightly for context
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 2)
                    cv2.putText(frame, name.upper(), (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 2)

        total_pedestrians = len(unique_pedestrians)

        # Risk level for this frame
        if person_count >= 5:
            risk_level = "HIGH"
            risk_color = (0, 0, 255)
        elif person_count >= 2:
            risk_level = "MEDIUM"
            risk_color = (0, 165, 255)
        elif person_count >= 1:
            risk_level = "LOW"
            risk_color = (0, 255, 0)
        else:
            risk_level = "CLEAR"
            risk_color = (100, 100, 100)

        lat += 0.000004
        lng += 0.000002

        # ── HUD ──
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 80), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 229, 255), 2)
        cv2.putText(frame, "MODULE: PEDESTRIAN SAFETY DETECTION", (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)
        cv2.putText(frame, f"Bus: {BUS_ID}", (width - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, f"GPS: {lat:.5f}, {lng:.5f}", (width - 300, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, height - 50), (width, height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0)

        cv2.putText(frame, f"Persons in Frame: {person_count}", (15, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Risk: {risk_level}", (300, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, risk_color, 2)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (width // 2 - 50, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
        
        cv2.putText(frame, f"Total Unique People: {total_pedestrians}", (width - 400, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. Total unique pedestrian detections: {total_pedestrians}")

if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "demo_pedestrians.mp4"
    if not os.path.exists(video):
        print(f"Video not found: {video}")
        sys.exit(1)
    run_demo(video)
