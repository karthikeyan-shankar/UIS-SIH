"""
demo_verification.py - Visual demo of the Spatial-Temporal Verification Process
Shows events going from UNCONFIRMED -> CONFIRMED as multiple buses report the same GPS cluster.
Run: python demo_verification.py
Press any key to advance through steps. Press 'q' to quit.
"""
import cv2
import numpy as np
import math
import time

WINDOW_NAME = "UIS - Spatial-Temporal Verification Demo"
W, H = 1280, 720

# Simulated GPS events from different buses hitting the same area
DEMO_EVENTS = [
    {"bus": "BUS_04", "type": "pothole", "lat": 11.0168, "lng": 76.9558, "conf": 0.82, "time": "14:22:10"},
    {"bus": "BUS_07", "type": "pothole", "lat": 11.0169, "lng": 76.9557, "conf": 0.78, "time": "14:35:44"},
    {"bus": "BUS_12", "type": "pothole", "lat": 11.0168, "lng": 76.9559, "conf": 0.91, "time": "15:01:22"},
]

# Colors
BLACK = (10, 10, 10)
DARK = (25, 25, 25)
CYAN = (255, 229, 0)
RED = (0, 0, 255)
GREEN = (0, 255, 0)
AMBER = (0, 180, 255)
WHITE = (230, 230, 230)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)


def draw_header(frame):
    cv2.rectangle(frame, (0, 0), (W, 60), (0, 25, 50), -1)
    cv2.line(frame, (0, 60), (W, 60), CYAN, 2)
    cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (20, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, CYAN, 2)
    cv2.putText(frame, "SPATIAL-TEMPORAL VERIFICATION MODULE", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 200), 1)


def draw_event_card(frame, x, y, event, status, highlight=False):
    """Draw an event card at position (x, y)."""
    card_w, card_h = 350, 140
    border_color = GREEN if status == "CONFIRMED" else RED if status == "UNCONFIRMED" else DARK_GRAY

    # Card background
    cv2.rectangle(frame, (x, y), (x + card_w, y + card_h), DARK, -1)
    cv2.rectangle(frame, (x, y), (x + card_w, y + card_h), border_color, 2)

    # Left status bar
    cv2.rectangle(frame, (x, y), (x + 5, y + card_h), border_color, -1)

    # Status badge
    badge_color = GREEN if status == "CONFIRMED" else RED
    cv2.rectangle(frame, (x + 15, y + 10), (x + 15 + len(status) * 13 + 10, y + 32), badge_color, -1)
    cv2.putText(frame, status, (x + 20, y + 27),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    # Event details
    cv2.putText(frame, f"Type: {event['type'].upper()}", (x + 15, y + 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1)
    cv2.putText(frame, f"Bus: {event['bus']}", (x + 15, y + 78),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, GRAY, 1)
    cv2.putText(frame, f"GPS: {event['lat']:.4f}, {event['lng']:.4f}", (x + 15, y + 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, GRAY, 1)
    cv2.putText(frame, f"Conf: {event['conf']:.0%}  |  {event['time']}", (x + 15, y + 122),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, GRAY, 1)

    if highlight:
        cv2.rectangle(frame, (x - 3, y - 3), (x + card_w + 3, y + card_h + 3), CYAN, 2)


def draw_cluster_visual(frame, num_buses, cx=900, cy=350):
    """Draw a GPS cluster visualization."""
    # Draw concentric circles for 15m radius
    cv2.circle(frame, (cx, cy), 80, DARK_GRAY, 1)
    cv2.circle(frame, (cx, cy), 40, DARK_GRAY, 1)
    cv2.putText(frame, "15m radius", (cx + 85, cy + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, GRAY, 1)

    # Draw bus dots
    bus_positions = [(cx - 15, cy - 10), (cx + 20, cy + 15), (cx - 5, cy + 25)]
    bus_colors = [GREEN, AMBER, CYAN]

    for i in range(min(num_buses, 3)):
        bx, by = bus_positions[i]
        cv2.circle(frame, (bx, by), 8, bus_colors[i], -1)
        cv2.circle(frame, (bx, by), 8, WHITE, 1)
        cv2.putText(frame, DEMO_EVENTS[i]['bus'], (bx + 12, by + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, bus_colors[i], 1)

    # Cluster center
    if num_buses >= 2:
        cv2.drawMarker(frame, (cx, cy), GREEN, cv2.MARKER_CROSS, 20, 2)
        cv2.putText(frame, "CLUSTER CENTER", (cx - 55, cy - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, GREEN, 1)

    # Label
    cv2.putText(frame, f"GPS Cluster ({num_buses}/2 buses)", (cx - 70, cy + 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)


def draw_formula(frame, y=600):
    """Draw the verification formula."""
    cv2.putText(frame, "Verification Rule:", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, CYAN, 1)
    cv2.putText(frame, "IF buses_reporting >= 2 AND distance < 15m THEN status = CONFIRMED", (20, y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1)


def run_demo():
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, W, H)

    steps = [
        "Step 1: BUS_04 reports a pothole. Only 1 bus = UNCONFIRMED",
        "Step 2: BUS_07 passes same area (12m away). Now 2 buses = CONFIRMED!",
        "Step 3: BUS_12 adds 3rd confirmation. High confidence cluster.",
    ]

    for step_idx in range(3):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = BLACK

        draw_header(frame)

        # Step title
        cv2.rectangle(frame, (0, 65), (W, 95), (20, 20, 20), -1)
        cv2.putText(frame, steps[step_idx], (20, 87),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, AMBER, 1)

        # Draw event cards based on current step
        for i in range(step_idx + 1):
            if step_idx == 0:
                status = "UNCONFIRMED"
            else:
                status = "CONFIRMED"

            highlight = (i == step_idx)
            draw_event_card(frame, 30, 110 + i * 160, DEMO_EVENTS[i], status, highlight)

        # Draw cluster visualization
        draw_cluster_visual(frame, step_idx + 1)

        # Draw connection arrows
        if step_idx >= 1:
            # Arrow from cards to cluster
            cv2.arrowedLine(frame, (390, 250), (780, 330), CYAN, 2, tipLength=0.03)
            cv2.putText(frame, "Haversine", (500, 280),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
            cv2.putText(frame, "distance < 15m", (500, 300),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)

        # Draw formula
        draw_formula(frame)

        # Bottom instruction
        cv2.rectangle(frame, (0, H - 35), (W, H), (20, 20, 20), -1)
        if step_idx < 2:
            cv2.putText(frame, "Press any key to advance  |  Press 'q' to quit", (W // 2 - 200, H - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, GRAY, 1)
        else:
            cv2.putText(frame, "VERIFICATION COMPLETE  |  Press any key to exit", (W // 2 - 200, H - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, GREEN, 1)

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(0)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()
    print("Verification demo complete.")


if __name__ == "__main__":
    run_demo()
