import json
import os
import glob
from verification import verify_events
from scoring import score_events

def validate_event(event):
    """Basic schema validation"""
    required_keys = ["event_id", "event_type", "timestamp", "gps", "confidence"]
    for key in required_keys:
        if key not in event:
            return False, f"Missing required key: {key}"
            
    if not isinstance(event['gps'], dict) or 'lat' not in event['gps'] or 'lng' not in event['gps']:
        return False, "Invalid gps format"
        
    if not (0 <= event['confidence'] <= 1):
        return False, "Confidence must be between 0 and 1"
        
    return True, ""

def run_pipeline():
    raw_files = glob.glob("raw/*.json")
    # Exclude the merged file itself from re-processing
    raw_files = [f for f in raw_files if not f.endswith("merged_events.json")]
    all_events = []
    
    print("[INTEGRATION] Starting pipeline...")
    
    # Merge and validate
    for file in raw_files:
        print(f" -> Processing {file}")
        with open(file, 'r') as f:
            events = json.load(f)
            
        valid_events = []
        for e in events:
            is_valid, err = validate_event(e)
            if is_valid:
                valid_events.append(e)
            else:
                print(f"    [WARNING] Dropping invalid event {e.get('event_id', 'unknown')}: {err}")
                
        all_events.extend(valid_events)
        
    # Write merged events
    merged_raw_path = 'raw/merged_events.json'
    with open(merged_raw_path, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2)
        
    print(f"[INTEGRATION] Merged {len(all_events)} valid events.")
    
    # Run Verification
    print("[INTEGRATION] Running Verification Module...")
    verify_events(merged_raw_path, 'confirmed/confirmed_events.json')
    
    # Run Scoring
    print("[INTEGRATION] Running Scoring Module...")
    score_events('confirmed/confirmed_events.json', 'ranked/ranked_events.json')
    
    print("[INTEGRATION] Pipeline complete! Data ready for dashboard.")
    return len(all_events)

def run_pipeline_and_return():
    """Run the full pipeline and return stats as a dict for the dashboard."""
    raw_count = run_pipeline()
    
    # Read back results
    confirmed = []
    ranked = []
    
    if os.path.exists('confirmed/confirmed_events.json'):
        with open('confirmed/confirmed_events.json', 'r') as f:
            confirmed = json.load(f)
    
    if os.path.exists('ranked/ranked_events.json'):
        with open('ranked/ranked_events.json', 'r') as f:
            ranked = json.load(f)
    
    return {
        "raw_count": raw_count,
        "confirmed_count": len(confirmed),
        "ranked_count": len(ranked),
        "confirmed_events": confirmed,
        "ranked_events": ranked
    }

if __name__ == "__main__":
    run_pipeline()
