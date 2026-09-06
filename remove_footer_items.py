import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove Footer Action and Footer Nav Items
footer_action_start = html.find('<!-- Footer Action -->')
if footer_action_start != -1:
    footer_nav_end = html.find('</nav>', footer_action_start)
    if footer_nav_end != -1:
        html = html[:footer_action_start] + html[footer_nav_end:]
        
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
