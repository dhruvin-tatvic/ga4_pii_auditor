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
                    dim = self.remove_event_prefix(leak.get('dimension', 'Unknown'))
                    if dim not in leak_summary_dict:
                        leak_summary_dict[dim] = {
                            "dimension": dim,
                            "count": 0,
                            "types": set()
                        }
                    leak_summary_dict[dim]["count"] += 1
                    if leak.get('type'):
                        leak_summary_dict[dim]["types"].add(leak.get('type'))
            
            leak_summary = [
                {
                    "dimension": v["dimension"],
                    "count": v["count"],
                    "type": ", ".join(sorted(v["types"]))
                }
                for v in leak_summary_dict.values()
            ]
            leak_summary.sort(key=lambda item: item["count"], reverse=True)
            
            total_leaks = len(leaks) if leaks else 0
            unique_dimensions = len(leak_summary_dict)
            pii_percentage = "N/A"
            if total_overall_count and total_overall_count > 0:
                calc_percentage = (total_leaks / total_overall_count) * 100
                if 0 < calc_percentage < 1:
                    pii_percentage = "<1%"
                else:
                    pii_percentage = f"{calc_percentage:.2f}%"

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
