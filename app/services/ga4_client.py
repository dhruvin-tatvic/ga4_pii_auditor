from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from app.utils.auth import get_oauth_creds
from app.services.pii_detector import PIIDetector

class GA4Client:
    def __init__(self):
        creds = get_oauth_creds()
        self.client = BetaAnalyticsDataClient(credentials=creds)
        self.pii_detector = PIIDetector()

    def audit_property(self, property_id, start_date, end_date, dimensions):
        property_path = f"properties/{property_id}"
        api_dimensions = [Dimension(name=dim) for dim in dimensions]
        metrics = [Metric(name="activeUsers")]
        request = RunReportRequest(
            property=property_path,
            dimensions=api_dimensions,
            metrics=metrics,
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        try:
            response = self.client.run_report(request)
        except Exception as e:
            print(f"Error querying GA4 property {property_id}: {e}")
            return []

        all_leaks = []
        seen_leaks = set()
        for row in response.rows:
            row_data = {}
            for i, dim_val in enumerate(row.dimension_values):
                row_data[dimensions[i]] = dim_val.value
            leaks = self.pii_detector.scan_row(row_data, dimensions)
            for leak in leaks:
                leak_sig = (leak["dimension"], leak["flagged_value"], leak["type"])
                if leak_sig not in seen_leaks:
                    seen_leaks.add(leak_sig)
                    all_leaks.append(leak)
        return all_leaks
