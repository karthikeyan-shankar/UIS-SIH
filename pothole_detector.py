import cv2
import json
import time
import uuid
import os
import random
from datetime import datetime
from transmission import TransmissionQueue

# We can import some utilities from the repo if needed, but the repo's run_eval is complex.
# We'll just define the shared event mapper here.

class PotholeVideoProcessor:
    def __init__(self, mock_api=True):
        self.mock_api = mock_api
        self.tx_queue = TransmissionQueue()
        # Simulated GPS for the bus
        self.current_lat = 11.0168
        self.current_lng = 76.9558
        self.bus_id = "bus_04"

    def process_video(self, video_source=0, frame_interval=15):
        """
        Process a video file or webcam stream.
        frame_interval: number of frames to skip before running inference (e.g. 15 for 0.5s at 30fps)
        """
        # If the user passes '0', it's the webcam.
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            print(f"Error opening video source: {video_source}")
            return

        frame_count = 0
        print(f"Starting pothole detection on source: {video_source}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Process every Nth frame
            if frame_count % frame_interval == 0:
                self._analyze_frame(frame)
                
            # Move bus slightly to simulate driving
            self.current_lat += 0.00001
            self.current_lng += 0.00001

        cap.release()
        print("Video processing complete.")

    def _analyze_frame(self, frame):
        # 1. Get raw output from the "model"
        if self.mock_api:
            raw_output = self._mock_model_inference()
        else:
            # Here you would encode the frame to base64 and call the OpenAI API 
            # exactly as the pothole-reporter repo does in run_eval.py
            print("Real API call not implemented without API Key.")
            raw_output = {"is_pothole": False}
            
        # 2. Check if it's a valid pothole detection
        if self._is_valid_pothole(raw_output):
            # 3. Convert to shared format
            event = self._format_event(raw_output)
            
            # 4. Transmit
            self.tx_queue.emit_event(event)

    def _mock_model_inference(self):
        """Mock the JSON response that would come from OpenAI in the repo."""
        # 10% chance to detect a pothole
        if random.random() < 0.10:
            return {
                "is_pothole": True,
                "looks_like_speed_breaker": False,
                "image_quality": "usable",
                "surface_type": "bituminous_asphalt",
                "on_drivable_surface": True,
                "has_localized_cavity": True,
                "has_broken_edge_or_rim": True,
                "has_depth_or_surface_loss": True,
                "temporal_consistency": "single_view",
                "size": random.choice(["small", "medium", "large"]),
                "description": "Simulated pothole detection for testing."
            }
        return {"is_pothole": False}

    def _is_valid_pothole(self, result):
        """Filter logic extracted from the repo's decision() function"""
        if not result or result.get("is_pothole") is not True:
            return False
        if result.get("looks_like_speed_breaker") is not False:
            return False
        if result.get("image_quality") != "usable":
            return False
        if result.get("on_drivable_surface") is not True:
            return False
        if result.get("has_localized_cavity") is not True:
            return False
        return True

    def _format_event(self, raw_result):
        """Wrapper to convert repo's native output into shared event JSON"""
        # We don't have area_px from the LLM, so we map the 'size' string to a severity hint.
        severity = raw_result.get("size", "medium")
        
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "event_type": "pothole",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gps": {
                "lat": round(self.current_lat, 5),
                "lng": round(self.current_lng, 5)
            },
            "bus_id": self.bus_id,
            "confidence": 0.85, # Hardcoded as API does not provide one
            "data": {
                "severity_hint": severity,
                "description": raw_result.get("description", "")
            }
        }
        return event

if __name__ == "__main__":
    # Create a dummy video file to test if none exists
    dummy_video = "test_video.avi"
    if not os.path.exists(dummy_video):
        import numpy as np
        out = cv2.VideoWriter(dummy_video, cv2.VideoWriter_fourcc(*'XVID'), 30, (640, 480))
        for _ in range(90): # 3 seconds of blank video
            out.write(np.zeros((480, 640, 3), dtype=np.uint8))
        out.release()
        
    processor = PotholeVideoProcessor(mock_api=True)
    processor.process_video(dummy_video, frame_interval=15)
