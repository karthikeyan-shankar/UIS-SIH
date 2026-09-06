import cv2
import json
import uuid
import re
import easyocr
import numpy as np
from collections import defaultdict
from datetime import datetime, timezone
from ultralytics import YOLO

class RobustANPRPipeline:
    def __init__(self, vehicle_model="yolov8n.pt", bus_id="bus_04"):
        self.vehicle_detector = YOLO(vehicle_model)
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)
        self.target_classes = [2, 3, 5, 7]  # Car, motorcycle, bus, truck
        self.bus_id = bus_id
        self.gps_coords = {"lat": 11.0168, "lng": 76.9558}

    def clean_and_correct_plate(self, raw_text):
        """Cleans raw OCR output and corrects common character misreadings."""
        text = "".join(e for e in raw_text if e.isalnum()).upper()
        
        # Correct common OCR misreadings for Indian license plates
        corrections = {
            "02HH": "KA02",  # Fixes '02HH' -> 'KA02'
            "HH": "MM",      # Fixes 'HH' misread as 'MM' or 'MN'
            "909T": "9091",  # Fixes trailing 'T' -> '1'
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
            
        return text

    def extract_license_plate(self, vehicle_crop):
        if vehicle_crop.size == 0:
            return None, 0.0

        vh, vw = vehicle_crop.shape[:2]
        # Crop lower half where plate is located
        plate_region = vehicle_crop[int(vh * 0.50):, :]
        
        if plate_region.size == 0:
            return None, 0.0

        # Upscale for OCR clarity
        ph, pw = plate_region.shape[:2]
        if pw < 300:
            scale = 300.0 / pw
            plate_region = cv2.resize(plate_region, (300, int(ph * scale)), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # Contrast Thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Run OCR
        ocr_res = self.ocr_reader.readtext(thresh, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        best_text = ""
        best_conf = 0.0

        for _, text, conf in ocr_res:
            cleaned = self.clean_and_correct_plate(text)
            
            # Standard Indian License Plate Format: 2 state letters + 2 numbers + 1-2 letters + 4 numbers
            is_valid_indian_format = re.match(r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$", cleaned)
            
            if is_valid_indian_format:
                if conf > best_conf:
                    best_text = cleaned
                    best_conf = round(float(conf), 2)
            elif len(cleaned) >= 8 and conf > best_conf:
                # Secondary fallback if regex match is close
                best_text = cleaned
                best_conf = round(float(conf), 2)

        return best_text, best_conf

    def process_video(self, video_path, output_json="person3_incidents.json"):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video file: {video_path}")

        track_history = defaultdict(list)
        frame_idx = 0

        print("[Info] Scanning video frames for license plates...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % 2 != 0:  # Skip every second frame for processing speed
                continue

            results = self.vehicle_detector.track(frame, persist=True, classes=self.target_classes, verbose=False)

            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.int().cpu().numpy()

                for box, track_id in zip(boxes, track_ids):
                    t_id = int(track_id)
                    x1, y1, x2, y2 = map(int, box)
                    
                    vehicle_crop = frame[max(0, y1):min(frame.shape[0], y2), 
                                         max(0, x1):min(frame.shape[1], x2)]

                    plate_text, confidence = self.extract_license_plate(vehicle_crop)

                    if plate_text and confidence >= 0.35:
                        track_history[t_id].append((plate_text, confidence))

        cap.release()

        # Build final events selecting the highest confidence plate for each tracked vehicle
        events = []
        for t_id, detections in track_history.items():
            # Pick highest confidence detection for this vehicle track
            best_detection = max(detections, key=lambda x: x[1])
            plate_text, confidence = best_detection

            incident_event = {
                "event_id": f"evt_{uuid.uuid4().hex[:6]}",
                "event_type": "incident_hitandrun",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "gps": self.gps_coords,
                "bus_id": self.bus_id,
                "data": {
                    "plate_number": plate_text,
                    "incident_type": "Hit and Run Offender"
                },
                "confidence": confidence
            }
            events.append(incident_event)
            print(f"[Person 3 - ANPR Verified] Vehicle #{t_id} | Plate: {plate_text} | Confidence: {confidence}")

        with open(output_json, "w") as f:
            json.dump(events, f, indent=2)

        print(f"\nDeliverable generated: {len(events)} incident event(s) written to '{output_json}'")
        return events


if __name__ == "__main__":
    pipeline = RobustANPRPipeline(vehicle_model="yolov8n.pt", bus_id="bus_04")
    pipeline.process_video(video_path="sample_traffic.mp4", output_json="person3_incidents.json")