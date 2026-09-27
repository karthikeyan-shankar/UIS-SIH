"""
demo_anpr.py - Live ANPR (Automatic Number Plate Recognition) Demo
Run: python demo_anpr.py "other modules/SHI/sample_traffic.mp4"
Press 'q' to quit
"""
import sys
import os
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

WINDOW_NAME = "UIS - ANPR Module"
BUS_ID = "bus_04"
GPS_LAT, GPS_LNG = 11.0178, 76.9562

def run_demo(video_path):
    model = YOLO("yolov8n.pt")

    # Try loading EasyOCR
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        ocr_available = True
        print("EasyOCR loaded successfully.")
    except ImportError:
        ocr_available = False
        print("[WARN] EasyOCR not installed. Will detect vehicles without plate reading.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = 0
    plates_detected = []
    lat, lng = GPS_LAT, GPS_LNG

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Run YOLO every 3rd frame (ANPR is heavier)
        if frame_count % 3 != 0:
            # Still show HUD on skipped frames
            _draw_hud(frame, width, height, frame_count, lat, lng, plates_detected)
            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        results = model(frame, verbose=False, conf=0.35)

        if results[0].boxes is not None:
            for box, cls_id, conf in zip(results[0].boxes.xyxy, results[0].boxes.cls, results[0].boxes.conf):
                name = model.names[int(cls_id)]
                x1, y1, x2, y2 = map(int, box)
                confidence = float(conf)

                if name in ["car", "bus", "truck", "motorcycle"]:
                    # Draw vehicle box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{name.upper()}", (x1, y1 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

                    # Try OCR on lower portion of vehicle (where plate usually is)
                    if ocr_available and (x2 - x1) > 60 and (y2 - y1) > 40:
                        plate_region_y1 = y1 + int((y2 - y1) * 0.80)
                        plate_crop = frame[plate_region_y1:y2, x1:x2]

                        if plate_crop.size > 0:
                            try:
                                ocr_results = reader.readtext(plate_crop, detail=1)
                                for (bbox_ocr, text, ocr_conf) in ocr_results:
                                    text = text.strip().upper().replace(" ", "")
                                    if len(text) >= 4 and ocr_conf > 0.3:
                                        # Draw plate highlight
                                        cv2.rectangle(frame, (x1, plate_region_y1), (x2, y2), (0, 255, 280), 3)

                                        # Plate text box
                                        plate_label = f"{text} ({ocr_conf:.0%})"
                                        cv2.rectangle(frame, (x1, y2), (x1 + len(plate_label) * 12 + 10, y2 + 30), (0, 180, 280), -1)
                                        cv2.putText(frame, plate_label, (x1 + 5, y2 + 22),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

                                        # Log it
                                        entry = f"{text} | {ocr_conf:.0%} | {datetime.now().strftime('%H:%M:%S')}"
                                        if entry not in [p.split(" | ")[0] for p in plates_detected[-10:]]:
                                            plates_detected.append(entry)
                                            print(f"  PLATE: {text} (conf: {ocr_conf:.2f})")
                            except Exception:
                                pass

        lat += 0.000004
        lng += 0.000002

        _draw_hud(frame, width, height, frame_count, lat, lng, plates_detected)

        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. Total plates captured: {len(plates_detected)}")


def _draw_hud(frame, width, height, frame_count, lat, lng, plates_detected):
    """Draw HUD overlay on frame."""
    # Top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
    frame_ref = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    np.copyto(frame, frame_ref)

    cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 229, 280), 3)
    cv2.putText(frame, "MODULE: ANPR - NUMBER PLATE RECOGNITION", (15, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 200), 2)

    cv2.putText(frame, f"Bus: {BUS_ID}", (width - 250, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
    cv2.putText(frame, f"GPS: {lat:.5f}, {lng:.5f}", (width - 250, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

    # Bottom bar
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, height - 60), (width, height), (0, 0, 0), -1)
    frame_ref2 = cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0)
    np.copyto(frame, frame_ref2)

    cv2.putText(frame, f"Plates Captured: {len(plates_detected)}", (15, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 280), 2)

    # Show last 3 plates on bottom right
    if plates_detected:
        recent = plates_detected[-3:]
        for i, p in enumerate(recent):
            cv2.putText(frame, p, (width - 350, height - 15 - (i * 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 180, 280), 1)

    timestamp = datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, timestamp, (width // 2 - 30, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (150, 150, 150), 2)


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "cityRoad_potHoles-side.mp4"
    if not os.path.exists(video):
        print(f"Video not found: {video}")
        sys.exit(1)
    run_demo(video)
