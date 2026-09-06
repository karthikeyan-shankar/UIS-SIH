# SIH Bus Sensing — My Build Spec (Team Lead's Side)

Deadline: **Sep 4**. This is the full technical scope for my part of the system, to be handed to an IDE/coding assistant as the working spec.

---

## Project context (one paragraph)

Bus-mounted cameras act as mobile urban sensors. Onboard, small AI models detect road defects, traffic density, pedestrian risk, and hit-and-run incidents; only compact event data (not raw video) is transmitted to a central dashboard. My part covers: pothole detection, the bandwidth-minimizing architecture, and two innovation layers (spatial-temporal verification + severity scoring) that sit between raw detections and the dashboard, plus integrating everyone else's module output into one working pipeline.

Team split (for context, not my build): Indira/Princy/Bala — person, pedestrian/school-crossing, and vehicle detection. Boomika — dashboard UI + ANPR/incident detection. Ashwin + me — video scripting and slides. Me — everything below.

---

## Shared data contract (every module, including mine, must follow this)

```json
{
  "event_id": "evt_00123",
  "event_type": "pothole",
  "timestamp": "2026-08-26T10:15:00Z",
  "gps": { "lat": 11.0168, "lng": 76.9558 },
  "bus_id": "bus_04",
  "data": { "area_px": 4200, "severity_hint": "medium" },
  "confidence": 0.91
}
```
- `event_type`: "pothole", "vehicle_count", "pedestrian_crossing", "incident_hitandrun", "missing_infra", etc.
- `data`: free-form per module, whatever's relevant to that detection
- `gps` + `timestamp`: always required, even placeholder values during dev
- `confidence`: always 0–1
- Output: one JSON file per module containing a list of these events (or CSV with matching columns)

---

## Module 1 — Pothole / Road Defect Detection (mine)

**Source**: an existing GitHub repo (already found — pothole detector, has both APK and source code, some updates applied by the original author). Adapt, don't rebuild.

**Tasks**:
1. Get the repo running locally on a sample road video file.
2. Check whether it outputs bounding boxes only, or segmentation (shape/area) — prefer area/shape data if available, since it feeds severity scoring later.
3. Test on varied conditions (dry road, wet road, shadowed road) to characterize false-positive behavior honestly — note this, it directly justifies the verification layer below.
4. Write a wrapper that converts the repo's native output into the shared event JSON format above (`event_type: "pothole"`), including a confidence score and (if available) an area value in `data`.
5. Decide a frame-sampling rate (e.g. process every Nth frame or every 0.5s) so it runs smoothly for a live demo on typical laptop hardware.

**Phase 2 (after static works)**: swap `cv2.VideoCapture(video_path)` for `cv2.VideoCapture(0)` to support a live webcam feed for the demo video. Detection loop and event emission logic stay the same.

**Deliverable**: script(s) that take a video (file or webcam) and emit pothole events in the shared format; one sample output file for integration testing.

---

## Module 2 — Bandwidth-Minimization Architecture (mine)

This is primarily a design/diagram deliverable, backed by a small real implementation to prove the concept — not a full network simulation.

**Design principles to implement/demonstrate**:
- **Edge-only processing**: detection runs locally; raw video never gets written to a "transmit" queue, only event JSON does.
- **Event-triggered transmission**: no data is sent when nothing is detected — only on a positive detection event.
- **Offline buffering**: events queue locally (e.g. append to a local file/log) if "network" is simulated as unavailable, and flush once "reconnected."
- **Priority ordering**: incident events (`event_type: "incident_hitandrun"`) should be flagged/sent ahead of routine defect events if a queue exists.

**What to actually build**: a small local "transmission" module — e.g. a function/queue that only writes an event to an `outbox/` folder when one is generated (not continuously), with a simple priority flag and a basic retry/buffer mechanism if the destination is unavailable. This is enough to demo and explain; it does not need real cellular network simulation.

**Deliverable**: a short script + a diagram (can be drawn separately, e.g. draw.io or similar) showing: on-device processing → event generation → priority queue → transmission, with raw video explicitly shown as never leaving the bus.

---

## Module 3 — Spatial-Temporal Verification (innovation layer, mine)

**Purpose**: turn noisy, single-frame detections into confirmed events by requiring multiple independent confirmations at the same location.

**Algorithm**:
1. Input: raw event files from detection modules (mine and teammates', all in shared format).
2. Cluster events by GPS proximity — group events within a fixed radius (~10–15 meters) of each other as the "same" real-world defect. Simple Euclidean/haversine distance is enough; no need for a full geospatial library unless one's already on hand.
3. Within each cluster, count independent detections (simulate "different bus passes" for the prototype — e.g. hardcode a few event files representing day 1 / day 2 / day 3 data).
4. Apply a threshold rule: if a cluster has ≥ N independent detections (e.g. N = 3, tunable), mark it `status: "confirmed"`; otherwise `status: "unconfirmed"`.
5. Output a new event list (same shared schema, with `status` field added, plus an aggregated confidence — e.g. average or max of contributing detections).

**Deliverable**: a script that takes one or more raw event files as input and outputs a `confirmed_events.json` file in the shared format with `status` added.

---

## Module 4 — Severity / Priority Scoring (innovation layer, mine)

**Purpose**: rank confirmed defects by urgency, not just list them.

**Formula (starting point, tune weights as needed)**:
```
severity_score = (0.4 * normalized_size) + (0.3 * normalized_recurrence) + (0.3 * normalized_traffic_volume)
```
- `normalized_size`: from pothole module's area/severity_hint data (or bounding box area as fallback), scaled 0–1
- `normalized_recurrence`: how many times a cluster was confirmed, scaled 0–1
- `normalized_traffic_volume`: pulled from the vehicle-counting module's output for that GPS area, scaled 0–1

**Deliverable**: a script that takes `confirmed_events.json` (+ vehicle-count data for traffic volume) and outputs a `ranked_events.json` — same schema, with `severity_score` added, sorted descending.

---

## Module 5 — Integration (mine, ongoing through the week)

**Responsibilities**:
1. Collect each teammate's output file as it becomes available.
2. Validate against the shared schema — check for `event_id`, `event_type`, `timestamp`, `gps`, `confidence` on every event; flag missing/malformed fields back to the module owner immediately.
3. Merge validated raw events from all modules into one combined pool.
4. Run the combined pool through Module 3 (verification) → Module 4 (severity scoring).
5. Provide `ranked_events.json` (and the raw/unconfirmed pool) to Boomika's dashboard as its data source.
6. Provide a hand-written fake sample events file (10–20 events, varied `event_type`s) to Boomika on day one so dashboard work isn't blocked waiting on real module output.

**Deliverable**: a small integration script/folder structure (`raw/`, `confirmed/`, `ranked/`) plus the fake sample file, checked in early.

---

## Build order (respecting Sep 4 deadline)

1. Fake sample events file → hand to Boomika immediately (unblocks dashboard).
2. Pothole detection on static video → working, emitting shared-format events.
3. Bandwidth/transmission module (small, can be done in parallel with #2).
4. Verification script (Module 3) — test against fake sample file first, then real pothole output.
5. Severity scoring script (Module 4) — needs vehicle-count data from teammates to fully work; can stub traffic volume with placeholder values until that's available.
6. Integration pass — swap fake file for real teammate outputs as they arrive, validate schema, feed dashboard.
7. Pothole live-webcam extension (stretch, only if time remains after 1–6 are solid).

---

## Self-check before presenting/building further

- Why an existing pothole model instead of training one, and what's its honest accuracy on test clips?
- Full frame-to-dashboard walkthrough: what data moves at each step, and what stays on the bus.
- Two detections 8m apart — same cluster or different? Why that radius?
- The three severity factors, and why those three specifically.
- What breaks if a teammate's file is missing `confidence`, and why the schema-first approach catches it early instead of late.
