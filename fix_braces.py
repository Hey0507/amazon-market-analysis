import re
with open('dashboard_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('{{', '{').replace('}}', '}')
content = content.replace('html_template = f"""', 'html_template = """')
content = content.replace('with open(DASHBOARD_FILE', 'html_template = html_template.replace("{json_data}", json_data)\n    with open(DASHBOARD_FILE')

with open('dashboard_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)
