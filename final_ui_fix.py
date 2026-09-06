import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Incidents and Reports to Top Nav
top_nav_end = html.find('</nav>', html.find('Command Center'))
if top_nav_end != -1:
    new_links = """
    <a class="h-full flex items-center font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors transition-all" href="#">
        Incidents
    </a>
    <a class="h-full flex items-center font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors transition-all" href="#">
        Reports
    </a>
    """
    html = html[:top_nav_end] + new_links + html[top_nav_end:]

# 2. Remove SideNavBar completely
sidebar_start = html.find('<!-- SideNavBar -->')
if sidebar_start != -1:
    # Find the closing </nav> for the sidebar
    sidebar_end = html.find('</nav>', sidebar_start)
    if sidebar_end != -1:
        html = html[:sidebar_start] + html[sidebar_end + 6:]

# 3. Change Map back to OSM and add CSS filter for dark mode
# Find the CartoDB URL and replace it with OSM
html = html.replace('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
html = html.replace('© CARTO', '')

# Inject CSS to invert the OSM map tiles to look like a sleek dark theme
css_injection = """
<style>
    /* Free Dark Mode Map using CSS inversion on OpenStreetMap */
    .leaflet-layer,
    .leaflet-control-zoom-in,
    .leaflet-control-zoom-out,
    .leaflet-control-attribution {
      filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
    }
</style>
</head>
"""
html = html.replace('</head>', css_injection)

# 4. Remove `ml-20` from the `<main>` tag since there's no left sidebar anymore
html = html.replace('ml-20', 'ml-0')
# Wait, let's just make sure it's fully fluid
html = html.replace('class="flex-1 ml-20 p-lg', 'class="flex-1 ml-0 p-lg')
html = html.replace('class="flex-1 p-lg', 'class="flex-1 ml-0 p-lg') # just in case

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
