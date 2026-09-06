import re

with open('stitch_light_ui.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Inject IDs for KPIs
html = html.replace('>3,421<', ' id="kpi-raw">3,421<')
html = html.replace('>124<', ' id="kpi-confirmed">124<')
html = html.replace('>88<', ' id="kpi-buses">88<')
html = html.replace('>12<', ' id="kpi-critical">12<')

# 2. Add ID to the map container and remove its mock content
map_start = html.find('<!-- Central Map Area (Leaflet Style Concept) -->')
if map_start != -1:
    div_start = html.find('<div', map_start)
    # Inject id="map"
    html = html[:div_start+4] + ' id="map"' + html[div_start+4:]
    
    # We need to remove the mock markers.
    # Leaflet will just inject its own elements into this div.
    # To keep it simple, we won't delete the inner html but we'll add a CSS rule to hide them if Leaflet initializes.
    # Actually, let's just use regex to remove everything inside this map div.
    pass

# 3. Add Leaflet CSS/JS to head
head_end = html.find('</head>')
leaflet_includes = """
    <!-- Leaflet.js (free, open-source maps - NO API key) -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
"""
html = html[:head_end] + leaflet_includes + html[head_end:]

# 4. Add Javascript logic to the end of the body
script_logic = """
<script>
    // ── Leaflet Map Init ──
    const map = L.map('map').setView([11.0168, 76.9558], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    const markers = L.markerClusterGroup();
    map.addLayer(markers);

    const TYPE_COLORS = {
        'pothole': '#a855f7',
        'incident_hitandrun': '#ef4444',
        'pedestrian_crossing': '#facc15',
        'vehicle_count': '#14b8a6',
        'missing_infra': '#64748b'
    };

    function createCircleIcon(color) {
        return L.divIcon({
            html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.4)"></div>`,
            className: '',
            iconSize: [14, 14],
            iconAnchor: [7, 7]
        });
    }

    async function loadDashboard() {
        try {
            const [statsRes, rawRes] = await Promise.all([
                fetch('/api/stats'),
                fetch('/api/raw')
            ]);
            const stats = await statsRes.json();
            const raw = await rawRes.json();

            document.getElementById('kpi-raw').textContent = stats.raw_count;
            document.getElementById('kpi-confirmed').textContent = stats.confirmed_count;
            document.getElementById('kpi-critical').textContent = stats.critical_count;
            document.getElementById('kpi-buses').textContent = stats.bus_count;

            markers.clearLayers();
            let hasCoords = false;
            raw.forEach(e => {
                const lat = e.gps?.lat;
                const lng = e.gps?.lng;
                if (lat && lng) {
                    hasCoords = true;
                    const color = TYPE_COLORS[e.event_type] || '#14b8a6';
                    const icon = createCircleIcon(color);
                    L.marker([lat, lng], { icon }).addTo(markers);
                }
            });
            if (hasCoords) {
                map.fitBounds(markers.getBounds().pad(0.1));
            }
        } catch (err) {
            console.error(err);
        }
    }
    
    // Clear out the mock HTML markers inside the map div right before Leaflet takes over
    document.querySelector('#map').innerHTML = '';

    setInterval(loadDashboard, 3000);
    loadDashboard();
</script>
</body>
"""

html = html.replace('</body>', script_logic)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
