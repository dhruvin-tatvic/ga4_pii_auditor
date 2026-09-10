import os

with open("app/services/ga4_client.py", "r") as f:
    content = f.read()

new_audit_property = """    def audit_property(self, property_id, start_date, end_date, dimensions):
        property_path = f"properties/{property_id}"
        metrics = [Metric(name="activeUsers")]
        
        email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_regex = r'\+?\d{1,3}?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        all_leaks = []
        seen_leaks = set()

        # GA4 allows maximum 9 dimensions per request. Chunk the dimensions.
        chunk_size = 9
        dimension_chunks = [dimensions[i:i + chunk_size] for i in range(0, len(dimensions), chunk_size)]

        for chunk_idx, dim_chunk in enumerate(dimension_chunks):
            api_dimensions = [Dimension(name=dim) for dim in dim_chunk]
            
            filter_expressions = []
            for dim in dim_chunk:
                for pattern in [email_regex, phone_regex]:
                    filter_expressions.append(
                        FilterExpression(
                            filter=Filter(
                                field_name=dim,
                                string_filter=Filter.StringFilter(
                                    match_type=Filter.StringFilter.MatchType.PARTIAL_REGEXP,
                                    value=pattern
                                )
                            )
                        )
                    )
                    
            or_group = FilterExpressionList(expressions=filter_expressions)
            dimension_filter = FilterExpression(or_group=or_group)

            request = RunReportRequest(
                property=property_path,
                dimensions=api_dimensions,
                metrics=metrics,
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimension_filter=dimension_filter,
            )
            
            try:
                response = self.client.run_report(request)
                
                for row in response.rows:
                    row_data = {}
                    for i, dim_val in enumerate(row.dimension_values):
                        row_data[dim_chunk[i]] = dim_val.value
                    leaks = self.pii_detector.scan_row(row_data, dim_chunk)
                    for leak in leaks:
                        leak_sig = (leak["dimension"], leak["flagged_value"], leak["type"])
                        if leak_sig not in seen_leaks:
                            seen_leaks.add(leak_sig)
                            all_leaks.append(leak)
                            
            except Exception as e:
                print(f"Error querying GA4 property {property_id} (Chunk {chunk_idx + 1}/{len(dimension_chunks)}): {e}")
                raise Exception(f"Failed to query GA4 property chunk: {e}")

        return all_leaks
"""

import re
# Replace the old audit_property with the new one
content = re.sub(r'    def audit_property\(self, property_id, start_date, end_date, dimensions\):.*', new_audit_property, content, flags=re.DOTALL)

with open("app/services/ga4_client.py", "w") as f:
    f.write(content)
