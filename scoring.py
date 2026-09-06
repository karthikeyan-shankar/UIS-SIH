"""
Severity / Priority Scoring Module
====================================
Ranks confirmed events by urgency using a weighted formula:

  severity_score = (0.4 × normalized_size) + (0.3 × normalized_recurrence) + (0.3 × normalized_traffic_volume)

- normalized_size: For potholes, based on area/severity_hint. For incidents = 1.0 (max danger).
- normalized_recurrence: How many buses independently confirmed this defect (0-1 scaled).
- normalized_traffic_volume: Pulled from nearby vehicle_count events (real data, not hardcoded).
"""
import json
import math
import os


def normalize(value, min_val, max_val):
    if max_val == min_val:
        return 0.5
    return max(0, min(1, (value - min_val) / (max_val - min_val)))


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_traffic_density(confirmed_dir):
    """Load vehicle density measurements saved by the verification module."""
    path = os.path.join(confirmed_dir, 'vehicle_density.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []


def get_traffic_volume_near(lat, lng, vehicle_events, radius_m=200):
    """Find the average vehicle count within radius_m of the given GPS point."""
    nearby_counts = []
    for v in vehicle_events:
        vlat = v.get('gps', {}).get('lat', 0)
        vlng = v.get('gps', {}).get('lng', 0)
        dist = haversine(lat, lng, vlat, vlng)
        if dist <= radius_m:
            count = v.get('data', {}).get('vehicle_count', 0)
            if isinstance(count, (int, float)) and count > 0:
                nearby_counts.append(count)
    
    if nearby_counts:
        return sum(nearby_counts) / len(nearby_counts)
    return 0


def score_events(confirmed_file, output_file):
    if not os.path.exists(confirmed_file):
        print(f"Error: {confirmed_file} not found.")
        return

    with open(confirmed_file, 'r') as f:
        events = json.load(f)

    # Load real vehicle density data
    confirmed_dir = os.path.dirname(confirmed_file)
    vehicle_events = load_traffic_density(confirmed_dir)
    
    # Calculate max traffic for normalization
    all_counts = [v.get('data', {}).get('vehicle_count', 0) for v in vehicle_events]
    all_counts = [c for c in all_counts if isinstance(c, (int, float)) and c > 0]
    max_traffic = max(all_counts) if all_counts else 1

    # Get max recurrence for normalization
    max_recurrence = max((e.get('confirmation_count', 1) for e in events), default=1)

    ranked_events = []

    for event in events:
        if event.get('status') != 'confirmed':
            continue

        event_type = event.get('event_type', '')

        # ── 1. Normalized Size / Danger ──
        if event_type == 'incident_hitandrun':
            normalized_size = 1.0  # Maximum danger — involves human safety
        elif event_type == 'pothole':
            hint = event.get('data', {}).get('severity_hint', 'medium')
            area = event.get('data', {}).get('area_px', 0)
            if area > 0:
                normalized_size = normalize(area, 0, 15000)
            else:
                # Use severity_hint as fallback
                hint_map = {'small': 0.3, 'medium': 0.6, 'large': 0.9}
                normalized_size = hint_map.get(hint, 0.5)
        elif event_type == 'pedestrian_crossing':
            normalized_size = 0.4  # Moderate — safety observation
        else:
            normalized_size = 0.5

        # ── 2. Normalized Recurrence ──
        count = event.get('confirmation_count', 1)
        normalized_recurrence = normalize(count, 0, max_recurrence)

        # ── 3. Normalized Traffic Volume (from REAL vehicle_count data) ──
        lat = event.get('gps', {}).get('lat', 0)
        lng = event.get('gps', {}).get('lng', 0)
        nearby_traffic = get_traffic_volume_near(lat, lng, vehicle_events)
        
        if nearby_traffic > 0:
            normalized_traffic = normalize(nearby_traffic, 0, max_traffic)
        else:
            # No vehicle data nearby — use a conservative estimate
            normalized_traffic = 0.5

        # ── Calculate Score ──
        severity_score = (0.4 * normalized_size) + (0.3 * normalized_recurrence) + (0.3 * normalized_traffic)

        scored_event = event.copy()
        scored_event['severity_score'] = round(severity_score, 3)
        scored_event['scoring_breakdown'] = {
            'size_factor': round(normalized_size, 3),
            'recurrence_factor': round(normalized_recurrence, 3),
            'traffic_factor': round(normalized_traffic, 3)
        }
        ranked_events.append(scored_event)

    # Sort descending — incidents first, then by score
    ranked_events.sort(key=lambda x: x['severity_score'], reverse=True)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ranked_events, f, indent=2)

    print(f"[SCORING] Ranked {len(ranked_events)} confirmed events.")
    if ranked_events:
        print(f"  Top event: {ranked_events[0]['event_type']} (score={ranked_events[0]['severity_score']})")
        print(f"  Bottom event: {ranked_events[-1]['event_type']} (score={ranked_events[-1]['severity_score']})")
    print(f" -> Output saved to {output_file}")


if __name__ == "__main__":
    score_events('confirmed/confirmed_events.json', 'ranked/ranked_events.json')
