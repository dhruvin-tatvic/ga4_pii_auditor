import os
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    def __init__(self):
        # We assume templates are in app/templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_report(self, client_name, property_id, start_date, end_date, leaks):
        template_data = {
            "client_name": client_name,
            "property_id": property_id,
            "start_date": start_date,
            "end_date": end_date,
            "leaks": leaks
        }
        if not leaks:
            template = self.env.get_template('clean_report.html')
        else:
            template = self.env.get_template('urgent_report.html')
        return template.render(template_data)
