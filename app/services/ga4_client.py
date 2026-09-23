import re

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from googleapiclient.discovery import build

from app.services.pii_detector import PIIDetector
from app.utils.auth import get_oauth_creds


class GA4Client:
    def __init__(self, access_email=None):
        creds = get_oauth_creds(access_email)

        self.client = BetaAnalyticsDataClient(credentials=creds)

        self.admin_service = build(
            'analyticsadmin',
            'v1beta',
            credentials=creds
        )

        self.pii_detector = PIIDetector()

    @staticmethod
    def _extract_invalid_dimension_name(error):
        """Extract the invalid dimension name from a GA4 InvalidArgument error."""
        message = str(error)

        match = re.search(
            r"Field\s+([^\s]+)\s+is not a valid dimension",
            message
        )

        if match:
            return match.group(1)

        return None

    def get_properties_list(self):
        try:
            properties = []

            request = self.admin_service.accountSummaries().list()
            response = request.execute()

            for account in response.get('accountSummaries', []):

                for propertySummary in account.get(
                    'propertySummaries',
                    []
                ):

                    properties.append({
                        "id": propertySummary.get(
                            "property"
                        ).split("/")[1],

                        "name": propertySummary.get(
                            "displayName"
                        ),

                        "account_name": account.get(
                            "displayName"
                        )
                    })

            return properties

        except Exception as e:
            print(f"Failed to fetch properties: {e}")
            return []

    def get_all_custom_dimensions(self, property_id):
        try:
            custom_dims = []

            response = (
                self.admin_service
                .properties()
                .customDimensions()
                .list(
                    parent=f"properties/{property_id}"
                )
                .execute()
            )

            for dim in response.get(
                'customDimensions',
                []
            ):

                scope = dim.get('scope')
                param_name = dim.get('parameterName')

                if scope == 'EVENT':
                    custom_dims.append(
                        f"customEvent:{param_name}"
                    )

                elif scope == 'USER':
                    custom_dims.append(
                        f"customUser:{param_name}"
                    )

                elif scope == 'ITEM':
                    custom_dims.append(
                        f"customItem:{param_name}"
                    )

            return custom_dims

        except Exception as e:
            print(
                f"Failed to fetch custom dimensions "
                f"for {property_id}: {e}"
            )

            return []

    def get_total_event_count(
        self,
        property_id,
        start_date,
        end_date
    ):
        """Fetch total event count from GA4 for the given date range."""

        try:
            property_path = f"properties/{property_id}"

            request = RunReportRequest(
                property=property_path,

                metrics=[
                    Metric(name="eventCount")
                ],

                date_ranges=[
                    DateRange(
                        start_date=start_date,
                        end_date=end_date
                    )
                ],
            )

            response = self.client.run_report(request)

            if response.rows:
                total_count = int(
                    response.rows[0]
                    .metric_values[0]
                    .value
                )

                return total_count

            return 0

        except Exception as e:
            print(
                f"Error fetching total event count "
                f"for {property_id}: {e}"
            )

            return 0

    def audit_property(
        self,
        property_id,
        start_date,
        end_date,
        dimensions
    ):
        property_path = f"properties/{property_id}"

        metrics = [
            Metric(name="eventCount")
        ]

        all_leaks = []
        seen_leaks = set()

        # GA4 Data API pagination size
        page_size = 10000

        for dim in dimensions:

            offset = 0

            try:

                while True:

                    request = RunReportRequest(
                        property=property_path,

                        dimensions=[
                            Dimension(name=dim)
                        ],

                        metrics=metrics,

                        date_ranges=[
                            DateRange(
                                start_date=start_date,
                                end_date=end_date
                            )
                        ],

                        # Explicit pagination
                        limit=page_size,
                        offset=offset
                    )

                    response = self.client.run_report(
                        request
                    )

                    rows_returned = len(
                        response.rows
                    )

                    total_rows = getattr(
                        response,
                        "row_count",
                        rows_returned
                    )

                    if not isinstance(total_rows, int):
                        total_rows = rows_returned

                    print(
                        f"GA4 dimension scan | "
                        f"dimension={dim} | "
                        f"offset={offset} | "
                        f"rows_returned={rows_returned} | "
                        f"total_rows={total_rows}"
                    )

                    # Scan every row returned by this page
                    for row in response.rows:

                        row_data = {
                            dim:
                                row.dimension_values[0].value
                                if row.dimension_values
                                else ""
                        }

                        leaks = (
                            self.pii_detector.scan_row(
                                row_data,
                                [dim]
                            )
                        )

                        for leak in leaks:

                            leak_sig = (
                                leak["dimension"],
                                leak["flagged_value"],
                                leak["type"]
                            )

                            if leak_sig not in seen_leaks:

                                seen_leaks.add(
                                    leak_sig
                                )

                                all_leaks.append(
                                    leak
                                )

                    # No rows means there is nothing
                    # more to retrieve.
                    if rows_returned == 0:
                        break

                    # All available rows have been retrieved.
                    if offset + rows_returned >= total_rows:
                        break

                    # Move to the next page.
                    offset += page_size

            except Exception as e:

                invalid_dim = (
                    self._extract_invalid_dimension_name(
                        e
                    )
                )

                if (
                    invalid_dim
                    and invalid_dim in dimensions
                ):

                    print(
                        f"Skipping invalid GA4 dimension: "
                        f"{invalid_dim} ({e})"
                    )

                    continue

                print(
                    f"Error querying GA4 property "
                    f"{property_id} for dimension "
                    f"{dim}: {e}"
                )

                raise Exception(
                    f"Failed to query GA4 property "
                    f"dimension: {e}"
                )

        print(
            f"GA4 property {property_id} "
            f"produced {len(all_leaks)} "
            f"unique PII leak(s)"
        )

        return all_leaks