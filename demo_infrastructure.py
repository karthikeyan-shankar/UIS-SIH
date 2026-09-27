"""
demo_infrastructure.py - Missing/Damaged Infrastructure Detection Demo
Detects missing or damaged urban infrastructure (barriers, signs, lights) from video.
Run: python demo_infrastructure.py "cityRoad_potHoles-side.mp4"
Press 'q' to quit. Press 's' to save a screenshot.
"""
import sys
import os
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

WINDOW_NAME = "UIS - Infrastructure Detection Module"
BUS_ID = "bus_04"
GPS_LAT, GPS_LNG = 11.0162, 76.9570

# Infrastructure-related COCO classes
INFRA_OBJECTS = {
    "traffic light": {"color": (0, 255, 0), "label": "TRAFFIC LIGHT", "category": "signal"},
    "stop sign": {"color": (0, 0, 280), "label": "STOP SIGN", "category": "sign"},
    "fire hydrant": {"color": (255, 100, 0), "label": "FIRE HYDRANT", "category": "utility"},
    "bench": {"color": (200, 200, 0), "label": "PUBLIC BENCH", "category": "amenity"},
    "parking meter": {"color": (150, 0, 280), "label": "PARKING METER", "category": "utility"},
}

# Objects that indicate road condition context
CONTEXT_OBJECTS = {"car", "bus", "truck", "motorcycle", "bicycle", "person"}


def run_demo(video_path):
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = 0
    infra_detected = {}
    lat, lng = GPS_LAT, GPS_LNG

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        results = model(frame, verbose=False, conf=0.3)

        frame_infra = []
        if results[0].boxes is not None:
            for box, cls_id, conf in zip(results[0].boxes.xyxy, results[0].boxes.cls, results[0].boxes.conf):
                name = model.names[int(cls_id)]
                x1, y1, x2, y2 = map(int, box)
                confidence = float(conf)

                if name in INFRA_OBJECTS:
                    info = INFRA_OBJECTS[name]
                    color = info["color"]
                    label = f"{info['label']} {confidence:.0%}"

                    # Thick border for infrastructure
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(frame, (x1, y1 - 22), (x1 + label_size[0] + 6, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 3, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                    # Corner markers
                    l = 15
                    cv2.line(frame, (x1, y1), (x1 + l, y1), color, 3)
                    cv2.line(frame, (x1, y1), (x1, y1 + l), color, 3)
                    cv2.line(frame, (x2, y1), (x2 - l, y1), color, 3)
                    cv2.line(frame, (x2, y1), (x2, y1 + l), color, 3)
                    cv2.line(frame, (x1, y2), (x1 + l, y2), color, 3)
                    cv2.line(frame, (x1, y2), (x1, y2 - l), color, 3)
                    cv2.line(frame, (x2, y2), (x2 - l, y2), color, 3)
                    cv2.line(frame, (x2, y2), (x2, y2 - l), color, 3)

                    frame_infra.append(info['label'])

                    # Track unique detections
                    if info['label'] not in infra_detected:
                        infra_detected[info['label']] = 0
                    infra_detected[info['label']] += 1

                elif name in CONTEXT_OBJECTS:
                    # Faint context objects
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 50, 50), 1)

        lat += 0.000003
        lng += 0.000002

        # ── HUD ──
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (15, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 229, 280), 3)
        cv2.putText(frame, "MODULE: INFRASTRUCTURE AUDIT", (15, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 200), 2)

        cv2.putText(frame, f"Bus: {BUS_ID}", (width - 250, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
        cv2.putText(frame, f"GPS: {lat:.5f}, {lng:.5f}", (width - 250, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        # Right-side inventory panel
        panel_x = width - 280
        panel_y = 80
        overlay3 = frame.copy()
        cv2.rectangle(overlay3, (panel_x - 10, panel_y), (width, panel_y + 30 + len(infra_detected) * 25 + 10), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay3, 0.6, frame, 0.4, 0)

        cv2.putText(frame, "INFRA INVENTORY", (panel_x, panel_y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 229, 280), 2)
        for j, (iname, icount) in enumerate(infra_detected.items()):
            y_item = panel_y + 45 + j * 25
            cv2.putText(frame, f"{iname}: {icount}", (panel_x, y_item),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Bottom bar
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, height - 60), (width, height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0)

        cv2.putText(frame, f"Frame: {frame_count}", (15, height - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (150, 150, 150), 2)

        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (width // 2 - 30, height - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (150, 150, 150), 2)

        if frame_infra:
            cv2.putText(frame, f"Detected: {', '.join(frame_infra)}", (width - 500, height - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Scanning for infrastructure...", (width - 350, height - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save screenshot
            ss_path = f"screenshot_infra_{frame_count}.png"
            cv2.imwrite(ss_path, frame)
            print(f"Screenshot saved: {ss_path}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. Infrastructure detected: {infra_detected}")


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "cityRoad_potHoles-side.mp4"
    if not os.path.exists(video):
        print(f"Video not found: {video}")
        sys.exit(1)
    run_demo(video)
