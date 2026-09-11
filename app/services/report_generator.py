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
            dimension_leak_count = {}
            if leaks:
                for leak in leaks:
                    key = (leak['dimension'], leak['type'])
                    leak_summary_dict[key] = leak_summary_dict.get(key, 0) + 1
                    
                    # Track leak count per dimension (for the new summary table)
                    dim = leak['dimension']
                    dimension_leak_count[dim] = dimension_leak_count.get(dim, 0) + 1
            
            leak_summary = [{"dimension": k[0], "type": k[1], "count": v} for k, v in leak_summary_dict.items()]
            
            # Create dimension summary for the new table (sorted by leak count descending)
            dimension_summary = [{"dimension": dim, "count": count} for dim, count in sorted(dimension_leak_count.items(), key=lambda x: x[1], reverse=True)]
            
            # Calculate unique dimensions count
            unique_dimensions_count = len(dimension_leak_count)
            total_leaks = len(leaks) if leaks else 0

            template_data = {
                "client_name": client_name,
                "property_id": property_id,
                "start_date": start_date,
                "end_date": end_date,
                "leak_summary": leak_summary,
                "total_leaks": total_leaks,
                "unique_dimensions_count": unique_dimensions_count,
                "dimension_summary": dimension_summary
            }
            if not leaks:
                template = self.env.get_template('clean_report.html')
            else:
                template = self.env.get_template('urgent_report.html')
            return template.render(template_data)
        except Exception as e:
            raise Exception(f"Report generation error: {e}")
