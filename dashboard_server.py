"""
Dashboard Server — Flask backend for the Urban Intelligence Platform.
Serves the HTML dashboard and exposes REST API endpoints for the frontend.
No Streamlit, no API keys, no external accounts needed.
"""
import json
import os
import glob
from flask import Flask, jsonify, render_template, send_from_directory
from integration_pipeline import run_pipeline_and_return

app = Flask(__name__, template_folder='templates')

# Base directory for the project data folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────── Pages ────────────────────────────

@app.route('/')
def index():
    return render_template('dashboard.html')

# ──────────────────────────── API ──────────────────────────────

def _load_json_folder(folder_name):
    """Load and merge all JSON files from a data folder."""
    folder = os.path.join(BASE_DIR, folder_name)
    if not os.path.exists(folder):
        return []
    
    all_events = []
    for filepath in glob.glob(os.path.join(folder, '*.json')):
        # Skip the merged file to avoid double-counting
        if os.path.basename(filepath) == 'merged_events.json':
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_events.extend(data)
                else:
                    all_events.append(data)
        except Exception:
            pass
    return all_events


@app.route('/api/raw')
def api_raw():
    """Return all raw (unprocessed) events from the raw/ folder."""
    events = _load_json_folder('raw')
    return jsonify(events)


@app.route('/api/confirmed')
def api_confirmed():
    """Return verified/clustered events from confirmed/ folder."""
    path = os.path.join(BASE_DIR, 'confirmed', 'confirmed_events.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/ranked')
def api_ranked():
    """Return severity-scored events from ranked/ folder."""
    path = os.path.join(BASE_DIR, 'ranked', 'ranked_events.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/stats')
def api_stats():
    """Return KPI summary for the dashboard header cards."""
    raw = _load_json_folder('raw')
    
    confirmed_path = os.path.join(BASE_DIR, 'confirmed', 'confirmed_events.json')
    confirmed = []
    if os.path.exists(confirmed_path):
        with open(confirmed_path, 'r', encoding='utf-8') as f:
            confirmed = json.load(f)
    
    ranked_path = os.path.join(BASE_DIR, 'ranked', 'ranked_events.json')
    ranked = []
    if os.path.exists(ranked_path):
        with open(ranked_path, 'r', encoding='utf-8') as f:
            ranked = json.load(f)
    
    # Count event types
    type_counts = {}
    for e in raw:
        t = e.get('event_type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Count incidents (hit-and-run)
    incidents = [e for e in raw if e.get('event_type') == 'incident_hitandrun']
    
    # Count unique buses
    buses = set(e.get('bus_id', '') for e in raw if e.get('bus_id'))
    
    # Count confirmed clusters
    confirmed_count = sum(1 for e in confirmed if e.get('status') == 'confirmed')
    
    # Critical alerts = high severity ranked events
    critical = sum(1 for e in ranked if e.get('severity_score', 0) >= 0.7)
    
    return jsonify({
        'raw_count': len(raw),
        'confirmed_count': confirmed_count,
        'ranked_count': len(ranked),
        'incident_count': len(incidents),
        'critical_count': critical,
        'bus_count': len(buses),
        'event_type_breakdown': type_counts,
        'incidents': incidents
    })


@app.route('/api/run-pipeline', methods=['POST'])
def api_run_pipeline():
    """Trigger the full integration pipeline and return results."""
    try:
        result = run_pipeline_and_return()
        return jsonify({'status': 'success', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ──────────────────────────── Run ──────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("  Urban Intelligence Dashboard")
    print("  Open your browser to: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
