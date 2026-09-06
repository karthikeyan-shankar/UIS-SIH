import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Give the alerts list an ID and clear its mock children
alerts_start = html.find('<!-- Alerts List (Scrollable) -->')
if alerts_start != -1:
    div_start = html.find('<div', alerts_start)
    html = html[:div_start+4] + ' id="alerts-list"' + html[div_start+4:]
    
    # We will clear this list from JS instead of using regex to find its end, to avoid breaking HTML.

# 2. Add IDs to the Pipeline status bars
html = html.replace('RAW 80%', '<span id="pipe-raw-text">RAW 100%</span>')
html = html.replace('style="width: 80%;"', 'id="pipe-raw" style="width: 100%;"')

html = html.replace('VERIFIED 60%', '<span id="pipe-verified-text">VERIFIED 0%</span>')
html = html.replace('style="width: 60%; margin-left: -80%;"', 'id="pipe-verified" style="width: 0%; margin-left: -100%;"')

html = html.replace('RANKED 20%', '<span id="pipe-ranked-text">RANKED 0%</span>')
html = html.replace('style="width: 20%; margin-left: -60%;"', 'id="pipe-ranked" style="width: 0%; margin-left: -0%;"')


# 3. Update the JavaScript logic
old_js_start = html.find('async function loadDashboard() {')
old_js_end = html.find('// Clear out the mock HTML markers', old_js_start)

new_js = """
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

            // 1. Update KPIs
            document.getElementById('kpi-raw').textContent = stats.raw_count;
            document.getElementById('kpi-confirmed').textContent = stats.confirmed_count;
            document.getElementById('kpi-critical').textContent = stats.critical_count;
            document.getElementById('kpi-buses').textContent = stats.bus_count;
            
            // 2. Update Pipeline Bar
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

            // 3. Update Map
            markers.clearLayers();
            let hasCoords = false;
            raw.forEach(e => {
                const lat = e.gps?.lat;
                const lng = e.gps?.lng;
                if (lat && lng) {
                    hasCoords = true;
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
            if (hasCoords && raw.length > 0) {
                // map.fitBounds(markers.getBounds().pad(0.1));
            }
            
            // 4. Update Live Alerts (Sidebar)
            const alertsList = document.getElementById('alerts-list');
            if (alertsList) {
                alertsList.innerHTML = ''; // Clear mock alerts
                
                if (ranked.length === 0) {
                    alertsList.innerHTML = '<div class="text-sm text-outline p-4 text-center">No ranked alerts yet. Pipeline is running.</div>';
                }
                
                ranked.forEach(alert => {
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
            }

        } catch (err) {
            console.error(err);
        }
    }
"""

html = html[:old_js_start] + new_js + html[old_js_end:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
