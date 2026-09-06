import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix the anchor tags in the top nav
nav_section_start = html.find('<!-- Center: Navigation Links -->')
nav_section_end = html.find('</nav>', nav_section_start)
if nav_section_start != -1 and nav_section_end != -1:
    nav_html = html[nav_section_start:nav_section_end]
    
    # We want to properly ID the three links and add the onclick attributes
    # 1. Command Center
    nav_html = re.sub(
        r'<a[^>]*Command Center\s*</a>',
        r'<a class="h-full flex items-center font-body-md text-body-md text-primary border-b-2 border-primary hover:text-primary-container transition-colors transition-all" href="#" id="nav-command" onclick="switchTab(\'command\')">Command Center</a>',
        nav_html, flags=re.IGNORECASE | re.DOTALL
    )
    
    # 2. Incidents
    nav_html = re.sub(
        r'<a[^>]*Incidents\s*</a>',
        r'<a class="h-full flex items-center font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors transition-all" href="#" id="nav-incidents" onclick="switchTab(\'incidents\')">Incidents</a>',
        nav_html, flags=re.IGNORECASE | re.DOTALL
    )
    
    # 3. Reports
    nav_html = re.sub(
        r'<a[^>]*Reports\s*</a>',
        r'<a class="h-full flex items-center font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors transition-all" href="#" id="nav-reports" onclick="switchTab(\'reports\')">Reports</a>',
        nav_html, flags=re.IGNORECASE | re.DOTALL
    )
    
    html = html[:nav_section_start] + nav_html + html[nav_section_end:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
