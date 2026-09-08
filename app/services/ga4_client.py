from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    FilterExpressionList,
    Filter,
)
from googleapiclient.discovery import build
from app.utils.auth import get_oauth_creds
from app.services.pii_detector import PIIDetector

class GA4Client:
    def __init__(self, access_email=None):
        creds = get_oauth_creds(access_email)
        self.client = BetaAnalyticsDataClient(credentials=creds)
        self.admin_service = build('analyticsadmin', 'v1beta', credentials=creds)
        self.pii_detector = PIIDetector()

    def get_properties_list(self):
        try:
            properties = []
            request = self.admin_service.accountSummaries().list()
            response = request.execute()
            for account in response.get('accountSummaries', []):
                for propertySummary in account.get('propertySummaries', []):
                    properties.append({
                        "id": propertySummary.get("property").split("/")[1],
                        "name": propertySummary.get("displayName"),
                        "account_name": account.get("displayName")
                    })
            return properties
        except Exception as e:
            print(f"Failed to fetch properties: {e}")
            return []

    def get_all_custom_dimensions(self, property_id):
        try:
            custom_dims = []
            response = self.admin_service.properties().customDimensions().list(
                parent=f"properties/{property_id}"
            ).execute()
            
            for dim in response.get('customDimensions', []):
                scope = dim.get('scope')
                param_name = dim.get('parameterName')
                if scope == 'EVENT':
                    custom_dims.append(f"customEvent:{param_name}")
                elif scope == 'USER':
                    custom_dims.append(f"customUser:{param_name}")
                elif scope == 'ITEM':
                    custom_dims.append(f"customItem:{param_name}")
            return custom_dims
        except Exception as e:
            print(f"Failed to fetch custom dimensions for {property_id}: {e}")
            return []

    def audit_property(self, property_id, start_date, end_date, dimensions):
        property_path = f"properties/{property_id}"
        metrics = [Metric(name="activeUsers")]
        
        email_regex = r'[a-zA-Z0-9_.+-]+(?:@|%40)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_regex = r'\b(?:(?:\+|%2B)(?:1|91)[-.\s%20])?\(?[2-9]\d{2}\)?[-.\s%20]+[2-9]\d{2}[-.\s%20]+\d{4}\b|\b(?:\+|%2B)(?:1|91)[-.\s%20][2-9]\d{9}\b'
        name_regex = r'(?:\b||-)(?:first_?name|last_?name|fname|lname|name)=([^&#\s]+)'
        
        all_leaks = []
        seen_leaks = set()

        chunk_size = 9
        dimension_chunks = [dimensions[i:i + chunk_size] for i in range(0, len(dimensions), chunk_size)]

        for chunk_idx, dim_chunk in enumerate(dimension_chunks):
            api_dimensions = [Dimension(name=dim) for dim in dim_chunk]
            
            filter_expressions = []
            for dim in dim_chunk:
                for pattern in [email_regex, phone_regex, name_regex]:
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
