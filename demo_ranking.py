"""
demo_ranking.py - Visual Severity Ranking Demo
Shows the ranked defect list with full scoring breakdown visible.
Run: python demo_ranking.py
Press any key to exit.
"""
import cv2
import numpy as np
import json
import os

WINDOW_NAME = "UIS - Severity Ranking Module"
W, H = 1280, 720

# Colors
BLACK = (10, 10, 10)
CYAN = (255, 229, 0)
RED = (0, 0, 255)
GREEN = (0, 255, 0)
AMBER = (0, 180, 255)
WHITE = (230, 230, 230)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
YELLOW = (0, 255, 255)

# If ranked data exists, use it. Otherwise use demo data.
DEMO_EVENTS = [
    {
        "event_type": "incident_hitandrun",
        "severity_score": 0.85,
        "status": "confirmed",
        "gps": {"lat": 11.0198, "lng": 76.9548},
        "bus_id": "bus_04",
        "confirmation_count": 1,
        "data": {"plate_number": "TN38AB4521", "incident_type": "Hit and Run"},
        "scoring_breakdown": {"size_factor": 1.0, "recurrence_factor": 0.5, "traffic_factor": 0.8},
        "reason": "Maximum danger (human safety) + High traffic zone"
    },
    {
        "event_type": "pothole",
        "severity_score": 0.72,
        "status": "confirmed",
        "gps": {"lat": 11.0170, "lng": 76.9560},
        "bus_id": "bus_07",
        "confirmation_count": 3,
        "data": {"severity_hint": "large", "description": "Large pothole on main road"},
        "scoring_breakdown": {"size_factor": 0.9, "recurrence_factor": 0.75, "traffic_factor": 0.5},
        "reason": "Large size + Confirmed by 3 buses + Moderate traffic"
    },
    {
        "event_type": "pothole",
        "severity_score": 0.61,
        "status": "confirmed",
        "gps": {"lat": 11.0155, "lng": 76.9575},
        "bus_id": "bus_12",
        "confirmation_count": 2,
        "data": {"severity_hint": "medium", "description": "Medium pothole near junction"},
        "scoring_breakdown": {"size_factor": 0.6, "recurrence_factor": 0.5, "traffic_factor": 0.7},
        "reason": "Medium size + High traffic junction area"
    },
    {
        "event_type": "pedestrian_crossing",
        "severity_score": 0.48,
        "status": "confirmed",
        "gps": {"lat": 11.0182, "lng": 76.9565},
        "bus_id": "bus_04",
        "confirmation_count": 1,
        "data": {"people_count": 6, "risk_level": "high"},
        "scoring_breakdown": {"size_factor": 0.4, "recurrence_factor": 0.3, "traffic_factor": 0.7},
        "reason": "High pedestrian density near busy road"
    },
    {
        "event_type": "pothole",
        "severity_score": 0.35,
        "status": "confirmed",
        "gps": {"lat": 11.0145, "lng": 76.9540},
        "bus_id": "bus_07",
        "confirmation_count": 1,
        "data": {"severity_hint": "small", "description": "Small surface crack"},
        "scoring_breakdown": {"size_factor": 0.3, "recurrence_factor": 0.25, "traffic_factor": 0.4},
        "reason": "Small defect + Low traffic area + Single report"
    },
]

TYPE_COLORS = {
    "incident_hitandrun": (0, 0, 220),
    "pothole": (0, 165, 255),
    "pedestrian_crossing": (200, 100, 255),
    "missing_infra": (255, 100, 50),
}


def get_severity_color(score):
    if score >= 0.7:
        return RED
    elif score >= 0.5:
        return AMBER
    else:
        return GREEN


def draw_score_bar(frame, x, y, value, label, color, bar_w=120):
    """Draw a horizontal score bar."""
    cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, GRAY, 1)
    bar_x = x + 65
    cv2.rectangle(frame, (bar_x, y - 10), (bar_x + bar_w, y + 2), (30, 30, 30), -1)
    fill_w = int(bar_w * value)
    cv2.rectangle(frame, (bar_x, y - 10), (bar_x + fill_w, y + 2), color, -1)
    cv2.putText(frame, f"{value:.0%}", (bar_x + bar_w + 5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, WHITE, 1)


def run_demo():
    # Try loading real ranked data
    ranked_path = os.path.join(os.path.dirname(__file__), "ranked", "ranked_events.json")
    if os.path.exists(ranked_path):
        with open(ranked_path, 'r') as f:
            events = json.load(f)
        # Add human-readable reasons
        for e in events:
            bd = e.get('scoring_breakdown', {})
            parts = []
            if bd.get('size_factor', 0) >= 0.7:
                parts.append("High danger")
            elif bd.get('size_factor', 0) >= 0.4:
                parts.append("Moderate size")
            else:
                parts.append("Small defect")

            rc = e.get('confirmation_count', 1)
            if rc >= 3:
                parts.append(f"Confirmed by {rc} buses")
            elif rc >= 2:
                parts.append(f"{rc} bus confirmations")
            else:
                parts.append("Single report")

            if bd.get('traffic_factor', 0) >= 0.7:
                parts.append("High traffic zone")
            elif bd.get('traffic_factor', 0) >= 0.4:
                parts.append("Moderate traffic")
            else:
                parts.append("Low traffic area")

            e['reason'] = " + ".join(parts)
    else:
        events = DEMO_EVENTS

    frame = np.zeros((H, W, 3), dtype=np.uint8)
    frame[:] = BLACK

    # Header
    cv2.rectangle(frame, (0, 0), (W, 60), (0, 25, 50), -1)
    cv2.line(frame, (0, 60), (W, 60), CYAN, 2)
    cv2.putText(frame, "URBAN INTELLIGENCE SYSTEM", (20, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, CYAN, 2)
    cv2.putText(frame, "SEVERITY RANKING MODULE", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 200), 1)

    # Formula
    cv2.rectangle(frame, (0, 65), (W, 95), (20, 20, 20), -1)
    cv2.putText(frame, "Score = (0.4 x Size) + (0.3 x Recurrence) + (0.3 x Traffic Volume)", (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, AMBER, 1)

    # Column headers
    y_start = 115
    cv2.putText(frame, "#", (15, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
    cv2.putText(frame, "TYPE", (40, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
    cv2.putText(frame, "SCORE", (200, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
    cv2.putText(frame, "SIZE", (290, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
    cv2.putText(frame, "RECUR", (450, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
    cv2.putText(frame, "TRAFFIC", (610, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)
    cv2.putText(frame, "REASONING", (780, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)

    cv2.line(frame, (10, y_start + 8), (W - 10, y_start + 8), DARK_GRAY, 1)

    # Draw ranked events
    row_h = 110
    max_display = min(len(events), 5)
    for i in range(max_display):
        e = events[i]
        y = y_start + 25 + i * row_h
        score = e.get('severity_score', 0)
        sev_color = get_severity_color(score)
        bd = e.get('scoring_breakdown', {})
        etype = e.get('event_type', 'unknown')
        type_color = TYPE_COLORS.get(etype, GRAY)

        # Row background (alternating)
        if i % 2 == 0:
            cv2.rectangle(frame, (5, y - 10), (W - 5, y + row_h - 20), (18, 18, 18), -1)

        # Rank number
        cv2.putText(frame, f"{i + 1}", (18, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)

        # Type badge
        type_label = etype.upper().replace("_", " ")
        cv2.rectangle(frame, (40, y), (40 + len(type_label) * 9 + 10, y + 22), type_color, -1)
        cv2.putText(frame, type_label, (45, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

        # Score
        cv2.putText(frame, f"{score:.2f}", (200, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, sev_color, 2)

        # Breakdown bars
        draw_score_bar(frame, 290, y + 15, bd.get('size_factor', 0), "Size", AMBER)
        draw_score_bar(frame, 450, y + 15, bd.get('recurrence_factor', 0), "Recur", GREEN)
        draw_score_bar(frame, 610, y + 15, bd.get('traffic_factor', 0), "Traf", CYAN)

        # Reasoning text
        reason = e.get('reason', '')
        # Word wrap at ~45 chars
        if len(reason) > 45:
            cv2.putText(frame, reason[:45], (780, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, WHITE, 1)
            cv2.putText(frame, reason[45:90], (780, y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.35, WHITE, 1)
        else:
            cv2.putText(frame, reason, (780, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.35, WHITE, 1)

        # GPS and bus info
        gps = e.get('gps', {})
        cv2.putText(frame, f"GPS: {gps.get('lat', 0):.4f}, {gps.get('lng', 0):.4f}  |  {e.get('confirmation_count', 1)} bus(es)",
                    (40, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.3, GRAY, 1)

        # Plate number for incidents
        if etype == "incident_hitandrun":
            plate = e.get('data', {}).get('plate_number', '')
            if plate:
                cv2.rectangle(frame, (40, y + 60), (40 + len(plate) * 12 + 10, y + 82), (0, 180, 255), -1)
                cv2.putText(frame, plate, (45, y + 77), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        # Separator
        cv2.line(frame, (10, y + row_h - 18), (W - 10, y + row_h - 18), (30, 30, 30), 1)

    # Bottom
    cv2.rectangle(frame, (0, H - 35), (W, H), (20, 20, 20), -1)
    cv2.putText(frame, f"Showing top {max_display} of {len(events)} ranked events  |  Press any key to exit",
                (W // 2 - 250, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, GRAY, 1)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, W, H)
    cv2.imshow(WINDOW_NAME, frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("Ranking demo complete.")


if __name__ == "__main__":
    run_demo()
