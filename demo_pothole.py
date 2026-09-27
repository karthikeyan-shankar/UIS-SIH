"""
demo_pothole.py - Fast Pothole Simulator + YOLO Vehicle Detection
"""
import sys
import os
import cv2
import numpy as np
from datetime import datetime
import random
from ultralytics import YOLO

WINDOW_NAME = "UIS - Pothole Detection Module"
BUS_ID = "bus_04"
GPS_LAT, GPS_LNG = 11.0171, 76.9558

class TrackedPothole:
    def __init__(self, width, height):
        self.x = random.randint(int(width * 0.35), int(width * 0.65))
        self.y = int(height * 0.55)
        self.w = random.randint(30, 50)
        self.h = random.randint(10, 20)
        self.speed_y = random.uniform(1.5, 3.0)
        self.active = True
        self.conf = random.uniform(0.72, 0.95)

    def update(self, max_height):
        self.y += self.speed_y
        self.speed_y *= 1.04 
        self.w *= 1.035
        self.h *= 1.035
        self.x -= (self.w * 0.01)
        if self.y > max_height:
            self.active = False

def run_demo(video_path):
    # Load Standard YOLOv8 to detect vehicles so we don't draw potholes on top of cars
    model = YOLO("yolov8n.pt")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = 0
    lat, lng = GPS_LAT, GPS_LNG

    total_potholes = 0
    active_potholes = []

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # 1. Detect Real Vehicles (Cars/Trucks) using YOLO
        results = model(frame, verbose=False, conf=0.3)
        vehicle_boxes = []
        
        if results[0].boxes is not None:
            for box, cls_id in zip(results[0].boxes.xyxy, results[0].boxes.cls):
                name = model.names[int(cls_id)]
                if name in ["car", "bus", "truck", "motorcycle"]:
                    vx1, vy1, vx2, vy2 = map(int, box)
                    vehicle_boxes.append((vx1, vy1, vx2, vy2))
                    
                    # Draw green box for vehicle
                    cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), (0, 255, 0), 2)
                    label = f"{name.upper()}"
                    cv2.putText(frame, label, (vx1, vy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 2. Spawn Simulated Potholes
        if random.random() < 0.03: 
            active_potholes.append(TrackedPothole(width, height))
            total_potholes += 1

        # 3. Draw Potholes (ONLY if they aren't on top of a vehicle)
        for p in active_potholes:
            p.update(height)
            if p.active:
                x1 = int(p.x)
                y1 = int(p.y)
                x2 = int(p.x + p.w)
                y2 = int(p.y + p.h)

                # Check if pothole is colliding with a vehicle bounding box
                is_under_vehicle = False
                for (vx1, vy1, vx2, vy2) in vehicle_boxes:
                    # If the center of the pothole is inside the vehicle box
                    cx, cy = x1 + (x2 - x1)//2, y1 + (y2 - y1)//2
                    if vx1 < cx < vx2 and vy1 < cy < vy2:
                        is_under_vehicle = True
                        break
                
                # Only draw if the road is clear
                if not is_under_vehicle:
                    color = (0, 0, 255) # Red for danger
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    
                    label = f"POTHOLE {p.conf:.0%}"
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0] + 5, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        active_potholes = [p for p in active_potholes if p.active]

        lat += 0.000003
        lng += 0.000002

        # ── HUD ──
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 80), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 229, 255), 2)
        cv2.putText(frame, "MODULE: POTHOLE DETECTION", (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)
        cv2.putText(frame, f"Bus: {BUS_ID}", (width - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, f"GPS: {lat:.5f}, {lng:.5f}", (width - 300, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, height - 50), (width, height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0)

        cv2.putText(frame, f"Frame: {frame_count}", (15, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (width // 2 - 50, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
        
        cv2.putText(frame, f"Total Potholes Detected: {total_potholes}", (width - 400, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow(WINDOW_NAME, frame)
        
        # Fast playback speed (cv2.waitKey(1)) as requested
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. Total potholes detected: {total_potholes}")

if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "cityRoad_potHoles-side.mp4"
    run_demo(video)
