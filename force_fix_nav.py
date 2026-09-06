import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

nav_section_start = html.find('<!-- Center: Navigation Links -->')
nav_section_end = html.find('</nav>', nav_section_start)

if nav_section_start != -1 and nav_section_end != -1:
    clean_nav = """<!-- Center: Navigation Links -->
<nav class="hidden md:flex gap-8 items-center h-full">
    <a class="h-full flex items-center font-body-md text-body-md text-primary border-b-2 border-primary hover:text-primary-container transition-colors transition-all" href="#" id="nav-command" onclick="switchTab('command')">
        Command Center
    </a>
    <a class="h-full flex items-center font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors transition-all" href="#" id="nav-incidents" onclick="switchTab('incidents')">
        Incidents
    </a>
    <a class="h-full flex items-center font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors transition-all" href="#" id="nav-reports" onclick="switchTab('reports')">
        Reports
    </a>
"""
    html = html[:nav_section_start] + clean_nav + html[nav_section_end:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
