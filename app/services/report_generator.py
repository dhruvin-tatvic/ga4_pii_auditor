import os
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    def __init__(self):
        # We assume templates are in app/templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_report(self, client_name, property_id, start_date, end_date, leaks):
        try:
            leak_summary_dict = {}
            if leaks:
                for leak in leaks:
                    key = (leak['dimension'], leak['type'])
                    leak_summary_dict[key] = leak_summary_dict.get(key, 0) + 1
            
            leak_summary = [{"dimension": k[0], "type": k[1], "count": v} for k, v in leak_summary_dict.items()]

            template_data = {
                "client_name": client_name,
                "property_id": property_id,
                "start_date": start_date,
                "end_date": end_date,
                "leak_summary": leak_summary,
                "total_leaks": len(leaks) if leaks else 0
            }
            if not leaks:
                template = self.env.get_template('clean_report.html')
            else:
                template = self.env.get_template('urgent_report.html')
            return template.render(template_data)
        except Exception as e:
            raise Exception(f"Report generation error: {e}")
