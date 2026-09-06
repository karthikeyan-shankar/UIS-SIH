import re

with open('stitch_light_ui.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Make the overall theme a bit darker (less blinding white) by changing body background
html = html.replace('bg-background text-on-background', 'bg-slate-200 text-slate-900')

# Inject IDs for KPIs
html = html.replace('>3,421<', ' id="kpi-raw">3,421<')
html = html.replace('>124<', ' id="kpi-confirmed">124<')
html = html.replace('>88<', ' id="kpi-buses">88<')
html = html.replace('>12<', ' id="kpi-critical">12<')

# Map Container
map_start = html.find('<!-- Central Map Area (Leaflet Style Concept) -->')
div_start = html.find('<div', map_start)
html = html[:div_start+4] + ' id="map"' + html[div_start+4:]

# Empty the map div so we don't need JS to do it (which broke leaflet)
# We find the end of the map div by looking for the start of the right sidebar
sidebar_start = html.find('<!-- Right Sidebar: Live Alerts (Fixed Width) -->')
# Find the closing tag of the map div (it's right before the sidebar)
map_end = html.rfind('</div>', 0, sidebar_start)
map_end = html.rfind('</div>', 0, map_end) # step back a couple divs to be safe...
# Actually, a regex is safer to just empty the div contents.
# But since HTML parsing with regex is bad, let's just use string slicing.
# The map div starts at div_start. Let's just find the first `<div class="absolute inset-0` and wipe everything from there to the end of the map div.
img_bg_start = html.find('<!-- Map Background Image Placeholder -->')
if img_bg_start != -1:
    end_of_map_markers = html.find('<!-- Right Sidebar', img_bg_start)
    # We want to keep the closing divs.
    # Let's just do it in JS, but BEFORE Leaflet initializes!

# Add Filter section to sidebar
header_end = html.find('<!-- Alerts List (Scrollable) -->')
filters_html = """
    <!-- Filters -->
    <div class="px-4 py-2 border-b border-outline-variant bg-surface-container-lowest">
        <div class="text-xs font-bold text-outline mb-2 uppercase">Filter Events</div>
        <div class="flex flex-wrap gap-2">
            <button onclick="toggleFilter('pothole')" id="filter-pothole" class="px-2 py-1 rounded text-xs font-bold bg-[#a855f7] text-white opacity-100 transition-opacity">Potholes</button>
            <button onclick="toggleFilter('incident')" id="filter-incident" class="px-2 py-1 rounded text-xs font-bold bg-[#ef4444] text-white opacity-100 transition-opacity">Incidents</button>
            <button onclick="toggleFilter('vehicle')" id="filter-vehicle" class="px-2 py-1 rounded text-xs font-bold bg-[#14b8a6] text-white opacity-100 transition-opacity">Vehicles</button>
            <button onclick="toggleFilter('pedestrian')" id="filter-pedestrian" class="px-2 py-1 rounded text-xs font-bold bg-[#facc15] text-slate-900 opacity-100 transition-opacity">Pedestrians</button>
        </div>
    </div>
"""
html = html[:header_end] + filters_html + html[header_end:]

# Setup alerts list ID
alerts_start = html.find('<!-- Alerts List (Scrollable) -->')
div_start = html.find('<div', alerts_start)
html = html[:div_start+4] + ' id="alerts-list"' + html[div_start+4:]

# Pipeline status bars
html = html.replace('RAW 80%', '<span id="pipe-raw-text">RAW 100%</span>')
html = html.replace('style="width: 80%;"', 'id="pipe-raw" style="width: 100%;"')
html = html.replace('VERIFIED 60%', '<span id="pipe-verified-text">VERIFIED 0%</span>')
html = html.replace('style="width: 60%; margin-left: -80%;"', 'id="pipe-verified" style="width: 0%; margin-left: -100%;"')
html = html.replace('RANKED 20%', '<span id="pipe-ranked-text">RANKED 0%</span>')
html = html.replace('style="width: 20%; margin-left: -60%;"', 'id="pipe-ranked" style="width: 0%; margin-left: -0%;"')

# Remove useless sidebar items (Left navigation)
# The user said "most of the features are usseless and then keep the essential alone".
# The left sidebar has icons. We can just leave them as decorative or hide the left navbar.
nav_start = html.find('<!-- Left Sidebar/Navigation (Fixed) -->')
nav_end = html.find('<!-- Main Content Area -->')
if nav_start != -1 and nav_end != -1:
    html = html[:nav_start] + html[nav_end:]
# Adjust main content margin since we removed the 20px left sidebar
html = html.replace('ml-20', 'ml-0')

# Head includes
head_end = html.find('</head>')
leaflet_includes = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
"""
html = html[:head_end] + leaflet_includes + html[head_end:]

# Script Logic
script_logic = """
<script>
    // 1. Wipe mock map content BEFORE Leaflet init
    document.querySelector('#map').innerHTML = '';

    // 2. Init Leaflet with CartoDB Dark Matter for striking contrast
    const map = L.map('map').setView([11.0168, 76.9558], 14);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors, © CARTO',
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

    // Filter State
    const activeFilters = {
        'pothole': true,
        'incident': true,
        'vehicle': true,
        'pedestrian': true
    };

    function toggleFilter(type) {
        activeFilters[type] = !activeFilters[type];
        const btn = document.getElementById('filter-' + type);
        if (activeFilters[type]) {
            btn.classList.remove('opacity-40');
            btn.classList.add('opacity-100');
        } else {
            btn.classList.remove('opacity-100');
            btn.classList.add('opacity-40');
        }
        loadDashboard(); // reload data with new filters
    }

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
            const [statsRes, rawRes, rankedRes] = await Promise.all([
                fetch('/api/stats'),
                fetch('/api/raw'),
                fetch('/api/ranked')
            ]);
            const stats = await statsRes.json();
            const raw = await rawRes.json();
            const ranked = await rankedRes.json();

            document.getElementById('kpi-raw').textContent = stats.raw_count;
            document.getElementById('kpi-confirmed').textContent = stats.confirmed_count;
            document.getElementById('kpi-critical').textContent = stats.critical_count;
            document.getElementById('kpi-buses').textContent = stats.bus_count;
            
            let raw_pct = 100;
            let verified_pct = stats.raw_count > 0 ? Math.round((stats.confirmed_count / stats.raw_count) * 100) : 0;
            let ranked_pct = stats.raw_count > 0 ? Math.round((stats.ranked_count / stats.raw_count) * 100) : 0;
            
            document.getElementById('pipe-raw').style.width = raw_pct + '%';
            document.getElementById('pipe-raw-text').textContent = 'RAW ' + stats.raw_count;
            document.getElementById('pipe-verified').style.width = verified_pct + '%';
            document.getElementById('pipe-verified').style.marginLeft = '-' + raw_pct + '%';
            document.getElementById('pipe-verified-text').textContent = 'VERIFIED ' + verified_pct + '%';
            document.getElementById('pipe-ranked').style.width = ranked_pct + '%';
            document.getElementById('pipe-ranked').style.marginLeft = '-' + verified_pct + '%';
            document.getElementById('pipe-ranked-text').textContent = 'RANKED ' + ranked_pct + '%';

            // Filter logic
            const isVisible = (evtType) => {
                if (evtType.includes('pothole')) return activeFilters['pothole'];
                if (evtType.includes('incident')) return activeFilters['incident'];
                if (evtType.includes('pedestrian')) return activeFilters['pedestrian'];
                if (evtType.includes('vehicle')) return activeFilters['vehicle'];
                return true;
            };

            markers.clearLayers();
            raw.forEach(e => {
                if (!isVisible(e.event_type)) return;
                
                const lat = e.gps?.lat;
                const lng = e.gps?.lng;
                if (lat && lng) {
                    const color = TYPE_COLORS[e.event_type] || '#14b8a6';
                    const icon = createCircleIcon(color);
                    let popupHtml = `<div style="font-family:system-ui;font-size:13px;min-width:180px;">
                        <b style="font-size:14px;text-transform:uppercase;color:${color}">${e.event_type.replace('_',' ')}</b><br/>
                        <b>Confidence:</b> ${(e.confidence * 100).toFixed(0)}%<br/>
                        <b>Time:</b> ${new Date(e.timestamp).toLocaleTimeString()}<br/>
                    </div>`;
                    L.marker([lat, lng], { icon }).bindPopup(popupHtml).addTo(markers);
                }
            });
            
            const alertsList = document.getElementById('alerts-list');
            if (alertsList) {
                alertsList.innerHTML = ''; 
                let count = 0;
                ranked.forEach(alert => {
                    if (!isVisible(alert.event_type)) return;
                    count++;
                    const typeColor = TYPE_COLORS[alert.event_type] || '#64748b';
                    let alertHtml = `
                    <div class="bg-surface-container-lowest border border-outline-variant/50 rounded-xl p-3 relative overflow-hidden group hover:bg-surface-container-low transition-colors cursor-pointer shadow-sm mb-3">
                        <div class="absolute left-0 top-0 bottom-0 w-1" style="background:${typeColor}"></div>
                        <div class="flex justify-between items-start mb-2 pl-2">
                            <div class="flex items-center gap-2">
                                <span class="font-label-caps text-label-caps" style="color:${typeColor}">${alert.event_type.replace('_', ' ').toUpperCase()}</span>
                            </div>
                            <span class="font-data-sm text-data-sm text-outline text-[10px]">Score: ${alert.severity_score.toFixed(2)}</span>
                        </div>
                        <p class="font-body-md text-body-sm text-on-surface mb-3 pl-2 text-sm">
                            Verified cluster of ${alert.confirmations} reports. 
                        </p>
                    </div>
                    `;
                    alertsList.insertAdjacentHTML('beforeend', alertHtml);
                });
                if (count === 0) {
                    alertsList.innerHTML = '<div class="text-sm text-outline p-4 text-center">No ranked alerts matching filters.</div>';
                }
            }

        } catch (err) {
            console.error(err);
        }
    }

    setInterval(loadDashboard, 3000);
    loadDashboard();
</script>
</body>
"""
html = html.replace('</body>', script_logic)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
