"""
Spatial-Temporal Verification Module
=====================================
Splits events by type and applies the correct strategy:
- Potholes / missing_infra: Cluster by GPS proximity, require ≥N bus confirmations
- Incidents (hit-and-run): Auto-confirm immediately (1 bus = enough), preserve ANPR data
- Pedestrian crossings: Pass through as individual observations (transient, not duplicates)
- Vehicle counts: Excluded — these are measurements, not anomalies. Stored separately for scoring.
"""
import json
import math
import os

# Configuration
CONFIRMATION_THRESHOLD = 2   # Potholes need ≥2 independent bus sightings
PROXIMITY_RADIUS_METERS = 15  # GPS clustering radius

# Event types that represent PERMANENT infrastructure defects (should be clustered)
CLUSTERABLE_TYPES = {"pothole", "missing_infra"}

# Event types that are CRITICAL and bypass verification (1 bus = confirmed)
IMMEDIATE_ESCALATION_TYPES = {"incident_hitandrun"}

# Event types that are transient observations (pass through, no clustering)
PASSTHROUGH_TYPES = {"pedestrian_crossing"}

# Event types that are measurements, not anomalies (excluded from verification output)
MEASUREMENT_TYPES = {"vehicle_count"}


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in meters between two points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def cluster_events(events):
    """Cluster events by GPS proximity within the same event_type."""
    clusters = []
    for event in events:
        lat = event['gps']['lat']
        lng = event['gps']['lng']
        matched_cluster = None

        for cluster in clusters:
            if cluster['event_type'] == event['event_type']:
                dist = haversine(lat, lng, cluster['center']['lat'], cluster['center']['lng'])
                if dist <= PROXIMITY_RADIUS_METERS:
                    matched_cluster = cluster
                    break

        if matched_cluster:
            matched_cluster['events'].append(event)
            n = len(matched_cluster['events'])
            matched_cluster['center']['lat'] = ((matched_cluster['center']['lat'] * (n-1)) + lat) / n
            matched_cluster['center']['lng'] = ((matched_cluster['center']['lng'] * (n-1)) + lng) / n
        else:
            clusters.append({
                'event_type': event['event_type'],
                'center': {'lat': lat, 'lng': lng},
                'events': [event]
            })
    return clusters


def verify_events(raw_events_file, output_file):
    if not os.path.exists(raw_events_file):
        print(f"Error: {raw_events_file} not found.")
        return

    with open(raw_events_file, 'r') as f:
        events = json.load(f)

    # ── Separate events by strategy ──
    clusterable = [e for e in events if e['event_type'] in CLUSTERABLE_TYPES]
    immediate   = [e for e in events if e['event_type'] in IMMEDIATE_ESCALATION_TYPES]
    passthrough = [e for e in events if e['event_type'] in PASSTHROUGH_TYPES]
    measurements = [e for e in events if e['event_type'] in MEASUREMENT_TYPES]

    verified_events = []

    # ── 1. Infrastructure defects: cluster + threshold ──
    clusters = cluster_events(clusterable)
    for cluster in clusters:
        event_count = len(cluster['events'])
        status = "confirmed" if event_count >= CONFIRMATION_THRESHOLD else "unconfirmed"
        base_event = sorted(cluster['events'], key=lambda x: x['timestamp'], reverse=True)[0]
        avg_confidence = sum(e.get('confidence', 0) for e in cluster['events']) / event_count
        
        # Collect unique bus IDs that saw this defect
        bus_ids = list(set(e.get('bus_id', '') for e in cluster['events']))

        verified_event = base_event.copy()
        verified_event['gps'] = cluster['center']
        verified_event['status'] = status
        verified_event['confidence'] = round(avg_confidence, 2)
        verified_event['confirmation_count'] = event_count
        verified_event['confirming_buses'] = bus_ids
        verified_events.append(verified_event)

    confirmed_defects = sum(1 for e in verified_events if e['status'] == 'confirmed')
    unconfirmed_defects = sum(1 for e in verified_events if e['status'] == 'unconfirmed')

    # ── 2. Incidents: auto-confirm, preserve ANPR data ──
    for event in immediate:
        verified_event = event.copy()
        verified_event['status'] = 'confirmed'
        verified_event['confirmation_count'] = 1
        verified_event['confirming_buses'] = [event.get('bus_id', '')]
        verified_events.append(verified_event)

    # ── 3. Pedestrian crossings: pass through as individual observations ──
    for event in passthrough:
        verified_event = event.copy()
        verified_event['status'] = 'confirmed'
        verified_event['confirmation_count'] = 1
        verified_event['confirming_buses'] = [event.get('bus_id', '')]
        verified_events.append(verified_event)

    # ── 4. Vehicle counts: save separately for scoring engine ──
    vehicle_count_path = os.path.join(os.path.dirname(output_file), 'vehicle_density.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(vehicle_count_path, 'w', encoding='utf-8') as f:
        json.dump(measurements, f, indent=2)

    # ── Save verified events ──
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(verified_events, f, indent=2)

    total_confirmed = sum(1 for e in verified_events if e['status'] == 'confirmed')
    print(f"[VERIFICATION] Processed {len(events)} raw events:")
    print(f"  Clusterable defects: {len(clusterable)} raw -> {len(clusters)} clusters -> {confirmed_defects} confirmed, {unconfirmed_defects} unconfirmed")
    print(f"  Incidents (auto-confirmed): {len(immediate)}")
    print(f"  Pedestrian observations: {len(passthrough)}")
    print(f"  Vehicle measurements (stored separately): {len(measurements)}")
    print(f"  TOTAL confirmed events: {total_confirmed}")
    print(f" -> Output saved to {output_file}")


if __name__ == "__main__":
    verify_events('raw/merged_events.json', 'confirmed/confirmed_events.json')
