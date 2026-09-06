import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove Top Nav items (Analytics, Asset Management)
# We can find them by their text and remove the anchor tag.
html = re.sub(r'<a[^>]*>\s*Analytics\s*</a>', '', html)
html = re.sub(r'<a[^>]*>\s*Asset Management\s*</a>', '', html)

# 2. Remove OPERATIONS Sector 7-G block
# It starts before the OPERATIONS text and ends after the Sector 7-G div
# Let's find the parent container.
# <!-- Top Action / Profile (Expands on hover) -->
# <div class="p-3 border-b border-outline-variant ... group-hover:bg-surface-container-low ...">
op_start = html.find('<!-- Top Action / Profile')
if op_start != -1:
    op_end = html.find('<!-- Primary Nav Items -->', op_start)
    if op_end != -1:
        html = html[:op_start] + html[op_end:]

# 3. Remove Data Layers
# <a ...>
# <span ...>layers</span>
# <span ...>Data Layers</span>
# </a>
html = re.sub(r'<a[^>]*>\s*<span[^>]*>layers</span>\s*<span[^>]*>Data Layers</span>\s*</a>', '', html, flags=re.DOTALL)

# 4. Remove Bottom Actions (Deploy Response, Support, System Health)
# <!-- Bottom Actions -->
bottom_start = html.find('<!-- Bottom Actions -->')
if bottom_start != -1:
    # Find the end of the sidebar. The sidebar is inside an <aside> or <nav> usually.
    # Let's find the closing tag of the <nav class="w-20 group hover:w-64 ...">
    # We can just remove everything from <!-- Bottom Actions --> to the closing </nav>
    bottom_end = html.find('</nav>', bottom_start)
    if bottom_end != -1:
        html = html[:bottom_start] + html[bottom_end:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
