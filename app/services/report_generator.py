import os
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    def __init__(self):
        # We assume templates are in app/templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        # Add custom filter to remove event prefixes
        self.env.filters['remove_prefix'] = self.remove_event_prefix

    def remove_event_prefix(self, value):
        """Remove event prefixes like 'customEvent:' from dimension names"""
        if isinstance(value, str) and ':' in value:
            return value.split(':', 1)[1]
        return value

    def generate_report(self, client_name, property_id, start_date, end_date, leaks, total_overall_count=None):
        try:
            leak_summary_dict = {}
            if leaks:
                for leak in leaks:
                    key = (leak['dimension'], leak['type'])
                    leak_summary_dict[key] = leak_summary_dict.get(key, 0) + 1
            
            leak_summary = [{"dimension": k[0], "type": k[1], "count": v} for k, v in leak_summary_dict.items()]
            
            total_leaks = len(leaks) if leaks else 0
            # Count unique dimension names (not dimension-type pairs)
            unique_dimensions = len(set(k[0] for k in leak_summary_dict.keys())) if leak_summary_dict else 0
            pii_percentage = 0
            if total_overall_count and total_overall_count > 0:
                pii_percentage = round((total_leaks / total_overall_count) * 100, 2)

            template_data = {
                "client_name": client_name,
                "property_id": property_id,
                "start_date": start_date,
                "end_date": end_date,
                "leak_summary": leak_summary,
                "total_leaks": total_leaks,
                "unique_dimensions": unique_dimensions,
                "pii_percentage": pii_percentage,
                "total_overall_count": total_overall_count
            }
            if not leaks:
                template = self.env.get_template('clean_report.html')
            else:
                template = self.env.get_template('urgent_report.html')
            return template.render(template_data)
        except Exception as e:
            raise Exception(f"Report generation error: {e}")
