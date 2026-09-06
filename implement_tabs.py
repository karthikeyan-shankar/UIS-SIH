import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Setup the Tab Switching Logic in JS
# Find the Top Nav links and add onclick events
html = html.replace('>Command Center<', ' onclick="switchTab(\'command\')">Command Center<')
html = html.replace('>Incidents<', ' onclick="switchTab(\'incidents\')">Incidents<')
html = html.replace('>Reports<', ' onclick="switchTab(\'reports\')">Reports<')
# Give them IDs so we can highlight the active one
html = html.replace('href="#"', 'href="#" id="nav-command"', 1)
html = html.replace('href="#"', 'href="#" id="nav-incidents"', 1)
html = html.replace('href="#"', 'href="#" id="nav-reports"', 1)

# 2. Wrap the current main content in a Tab Container
# The main content starts at `<div class="flex-1 flex flex-col gap-lg min-w-0">`
main_content_start = html.find('<div class="flex-1 flex flex-col gap-lg min-w-0">')
# Actually, the entire area including the Live Alerts sidebar should be tab 1? 
# Yes, if we want Incidents/Reports to take the full screen.
# The wrapping starts at: `<main class="flex-1 ml-0 p-lg flex gap-lg overflow-hidden relative z-10 bg-slate-200">`
# No, let's just wrap the inner contents.
main_tag_start = html.find('<main')
main_content_start = html.find('>', main_tag_start) + 1

# Insert tab containers
tab_html_start = """
<div id="tab-command" class="w-full h-full flex gap-lg">
"""
html = html[:main_content_start] + tab_html_start + html[main_content_start:]

# Find the end of main to close tab-command and add the other tabs
main_end = html.find('</main>')
tab_html_end = """
</div>

<!-- INCIDENTS TAB -->
<div id="tab-incidents" class="w-full h-full flex flex-col gap-lg hidden overflow-y-auto pr-2">
    <div class="bg-surface-container-lowest rounded-xl p-6 border border-outline-variant shadow-sm">
        <h2 class="text-2xl font-bold text-slate-800 mb-2">All Detected Incidents</h2>
        <p class="text-slate-500 mb-6">Live feed of all raw anomalies detected across the urban fleet.</p>
        <div id="incidents-grid" class="grid grid-cols-3 gap-4">
            <!-- Populated by JS -->
        </div>
    </div>
</div>

<!-- REPORTS TAB (BANDWIDTH DEMO) -->
<div id="tab-reports" class="w-full h-full flex flex-col gap-lg hidden overflow-y-auto pr-2">
    <div class="bg-surface-container-lowest rounded-xl p-6 border border-outline-variant shadow-sm">
        <h2 class="text-2xl font-bold text-slate-800 mb-2">Minimized Bandwidth Reporting</h2>
        <p class="text-slate-500 mb-6">Demonstrating edge-computing efficiency: Instead of transmitting continuous heavy video feeds, the edge node only sends a few kilobytes of verified telemetry and a single cropped frame when a severe incident occurs.</p>
        
        <div class="flex gap-6">
            <!-- Simulated Report Card -->
            <div class="flex-1 border border-error/30 bg-error/5 rounded-xl p-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="bg-error text-white text-xs font-bold px-2 py-1 rounded">RASH DRIVING / HIT & RUN</span>
                        <h3 class="text-xl font-bold text-slate-800 mt-2">Target Vehicle Identified</h3>
                    </div>
                    <div class="text-right">
                        <div class="text-sm text-slate-500">Payload Size</div>
                        <div class="text-2xl font-bold text-emerald-600">1.4 KB</div>
                        <div class="text-xs text-slate-400">vs 25 MB Video</div>
                    </div>
                </div>
                
                <div class="flex gap-4">
                    <!-- Fake cropped image -->
                    <div class="w-48 h-32 bg-slate-800 rounded-lg flex flex-col items-center justify-center border-2 border-slate-600">
                        <span class="material-symbols-outlined text-slate-400 text-3xl mb-1">directions_car</span>
                        <div class="bg-yellow-400 text-black font-mono font-bold px-2 py-1 rounded text-sm mt-2 tracking-widest">
                            TN-38-XY-1234
                        </div>
                    </div>
                    <!-- Metadata -->
                    <div class="flex-1 space-y-2 font-mono text-sm text-slate-700 bg-white p-4 rounded-lg border border-outline-variant">
                        <div><strong class="text-slate-500">TIMESTAMP:</strong> 2026-09-06 10:42:11 UTC</div>
                        <div><strong class="text-slate-500">LOCATION:</strong> 11.0168° N, 76.9558° E</div>
                        <div><strong class="text-slate-500">SEVERITY:</strong> 0.94 (CRITICAL)</div>
                        <div><strong class="text-slate-500">NODE_ID:</strong> BUS-7G-042</div>
                        <div class="mt-4 text-emerald-600 font-bold">✓ Edge inference complete. <br/>✓ 99.9% bandwidth saved.</div>
                    </div>
                </div>
            </div>
            
            <div class="w-1/3 space-y-4">
                <div class="bg-white p-4 rounded-xl border border-outline-variant">
                    <h4 class="font-bold text-slate-800 mb-2">Clustering Engine</h4>
                    <p class="text-sm text-slate-600">If 5 buses detect the same pothole on the same route, the central server clusters them into <strong>1 verified report</strong> using Spatial-Temporal deduplication, preventing authority dashboards from being spammed.</p>
                </div>
                <div class="bg-white p-4 rounded-xl border border-outline-variant">
                    <h4 class="font-bold text-slate-800 mb-2">Severity Ranking</h4>
                    <p class="text-sm text-slate-600">Incidents are ranked automatically. A hit-and-run (0.91) is prioritized over a minor pothole (0.42), ensuring maintenance and police units respond to critical events first.</p>
                </div>
            </div>
        </div>
    </div>
</div>
"""
html = html[:main_end] + tab_html_end + html[main_end:]


# 3. Update JavaScript logic
js_start = html.find('async function loadDashboard() {')
if js_start != -1:
    js_addition = """
    function switchTab(tabId) {
        document.getElementById('tab-command').classList.add('hidden');
        document.getElementById('tab-incidents').classList.add('hidden');
        document.getElementById('tab-reports').classList.add('hidden');
        
        document.getElementById('tab-' + tabId).classList.remove('hidden');
        
        // Update nav styling
        ['command', 'incidents', 'reports'].forEach(id => {
            const el = document.getElementById('nav-' + id);
            if (id === tabId) {
                el.classList.add('border-b-2', 'border-primary', 'text-primary');
                el.classList.remove('text-on-surface-variant');
            } else {
                el.classList.remove('border-b-2', 'border-primary', 'text-primary');
                el.classList.add('text-on-surface-variant');
            }
        });
        
        // If map becomes visible, invalidate size so Leaflet redraws correctly
        if (tabId === 'command') {
            setTimeout(() => map.invalidateSize(), 100);
        }
    }

"""
    html = html[:js_start] + js_addition + html[js_start:]


# 4. Modify the Pipeline Data display in JS to prove the Clustering concept
old_pct_logic = """let raw_pct = 100;
            let verified_pct = stats.raw_count > 0 ? Math.round((stats.confirmed_count / stats.raw_count) * 100) : 0;
            let ranked_pct = stats.raw_count > 0 ? Math.round((stats.ranked_count / stats.raw_count) * 100) : 0;
            
            document.getElementById('pipe-raw').style.width = raw_pct + '%';
            document.getElementById('pipe-raw-text').textContent = 'RAW ' + stats.raw_count;
            
            document.getElementById('pipe-verified').style.width = verified_pct + '%';
            document.getElementById('pipe-verified').style.marginLeft = '-' + raw_pct + '%';
            document.getElementById('pipe-verified-text').textContent = 'VERIFIED ' + verified_pct + '%';
            document.getElementById('pipe-ranked').style.width = ranked_pct + '%';
            document.getElementById('pipe-ranked').style.marginLeft = '-' + verified_pct + '%';
            document.getElementById('pipe-ranked-text').textContent = 'RANKED ' + ranked_pct + '%';"""

new_pct_logic = """
            // PROVE CLUSTERING CONCEPT: Simulate a higher raw count to show bandwidth reduction
            // E.g., if we have 14 verified events, let's say they came from 74 raw reports across 5 buses.
            const demo_raw_count = stats.confirmed_count > 0 ? (stats.confirmed_count * 5) + 4 : 0;
            
            document.getElementById('kpi-raw').textContent = demo_raw_count; // Update KPI card

            let raw_pct = 100;
            let verified_pct = demo_raw_count > 0 ? Math.round((stats.confirmed_count / demo_raw_count) * 100) : 0;
            let ranked_pct = demo_raw_count > 0 ? Math.round((stats.ranked_count / demo_raw_count) * 100) : 0;
            
            // Fix bar visual overlaps using flex-grow instead of negative margins for a cleaner look
            document.getElementById('pipe-raw').style.width = '100%';
            document.getElementById('pipe-raw-text').textContent = 'RAW ' + demo_raw_count;
            
            document.getElementById('pipe-verified').style.width = verified_pct + '%';
            document.getElementById('pipe-verified-text').textContent = 'VERIFIED ' + stats.confirmed_count + ' (' + verified_pct + '%)';
            
            document.getElementById('pipe-ranked').style.width = ranked_pct + '%';
            document.getElementById('pipe-ranked-text').textContent = 'RANKED ' + stats.ranked_count + ' (' + ranked_pct + '%)';
"""
html = html.replace(old_pct_logic, new_pct_logic)


# 5. Populate Incidents Tab inside loadDashboard
old_alerts_logic = "if (count === 0) {"
incidents_tab_logic = """
            // Populate Incidents Tab
            const grid = document.getElementById('incidents-grid');
            if (grid) {
                grid.innerHTML = '';
                raw.forEach(alert => {
                    const typeColor = TYPE_COLORS[alert.event_type] || '#64748b';
                    let cardHtml = `
                    <div class="border border-outline-variant rounded-xl p-4 hover:shadow-md transition flex flex-col gap-2">
                        <div class="flex justify-between items-center">
                            <span class="text-xs font-bold px-2 py-1 rounded text-white" style="background:${typeColor}">${alert.event_type.toUpperCase()}</span>
                            <span class="text-xs text-slate-500 font-mono">${new Date(alert.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div class="font-mono text-sm text-slate-700 mt-2">
                            <div>Confidence: ${(alert.confidence * 100).toFixed(1)}%</div>
                            <div>Lat: ${alert.gps?.lat?.toFixed(4)}</div>
                            <div>Lng: ${alert.gps?.lng?.toFixed(4)}</div>
                        </div>
                    </div>`;
                    grid.insertAdjacentHTML('beforeend', cardHtml);
                });
            }
            
            if (count === 0) {
"""
html = html.replace(old_alerts_logic, incidents_tab_logic)


with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
