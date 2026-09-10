import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.utils.auth import get_oauth_creds
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

def test_regex_filter():
    creds = get_oauth_creds()
    client = BetaAnalyticsDataClient(credentials=creds)
    
    # regex for testing: something simple
    # email regex: [a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+
    regex_pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    
    # We create a filter expression for the dimension pageLocation
    dimension_filter = FilterExpression(
        filter=Filter(
            field_name="pageLocation",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.PARTIAL_REGEXP,
                value=regex_pattern,
            )
        )
    )
    
    request = RunReportRequest(
        property="properties/360918272",
        dimensions=[Dimension(name="pageLocation")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        dimension_filter=dimension_filter,
    )
    
    try:
        response = client.run_report(request)
        print("Regex Query Response:")
        for row in response.rows:
            print(f"Location: {row.dimension_values[0].value}, Users: {row.metric_values[0].value}")
        if not response.rows:
            print("No rows returned (which means the regex query ran successfully but found nothing matching).")
    except Exception as e:
        print(f"Error querying GA4 Data API: {e}")

if __name__ == "__main__":
    test_regex_filter()
