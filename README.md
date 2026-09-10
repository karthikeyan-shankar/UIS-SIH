# Urban Intelligence System (UIS) - SIH 2026

## Project Overview
The Urban Intelligence System is a smart, mobile edge-computing platform designed to transform public transport buses into mobile sensor networks. By tapping into the government-mandated AIS-140 camera and GPS systems on public buses, the UIS platform utilizes edge-AI to detect urban anomalies such as potholes, traffic violations, and accidents in real-time.

## Key Features
- **Edge AI Processing:** Utilizes YOLOv8 for object detection and EasyOCR for ANPR (Automatic Number Plate Recognition) entirely on edge hardware.
- **Bandwidth Optimization:** Employs a Store and Forward architecture, sending 1.4KB JSON payloads instead of heavy video streams—saving 99.9% of telemetry bandwidth.
- **Spatial Event Deduplication:** Implements Haversine distance-based clustering to merge duplicate reports (e.g., the same pothole detected by multiple buses).
- **Priority Scoring:** Ranks incidents based on severity, traffic density, and frequency for optimized municipal response.
- **Live Command Center:** A secure, high-contrast dashboard for municipal and traffic authorities to visualize and action intelligence.

## Technical Architecture
1. **Onboard Edge Unit:**
   - Captures video frames from existing bus cameras.
   - Runs `pothole_detector.py` and ANPR models locally.
   - Outputs standardized JSON events.
2. **Central Intelligence Server:**
   - Receives encrypted payloads (`transmission.py`).
   - Clusters and verifies events (`verification.py`).
   - Scores events using local traffic density maps (`scoring.py`).
   - Serves the unified Command Center (`dashboard_server.py`).

## Setup Instructions

### Requirements
- Python 3.9+
- YOLOv8 (Ultralytics)
- OpenCV
- Flask
- EasyOCR

### Running the System
1. **Start the Dashboard:**
   ```bash
   python dashboard_server.py
   ```
   *Dashboard will be available at http://localhost:5000*

2. **Run the Core Pipeline:**
   ```bash
   python integration_pipeline.py
   ```
   *This script runs the spatial clustering and verification pipeline on raw data.*

## License
Proprietary - Developed for Smart India Hackathon (SIH) 2026.
