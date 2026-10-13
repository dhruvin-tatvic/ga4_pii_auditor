import re

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)
from googleapiclient.discovery import build

from app.services.pii_detector import PIIDetector
from app.utils.auth import get_oauth_creds

# Server-side GA4 RE2 regex pre-filter for candidate PII.
# Matches emails (@ or %40) or phone keywords with assignment delimiters.
GA4_PII_CANDIDATE_REGEX = (
    r"(@|%40|\b(phone(_?number|_?no)?|mobile(_?number|_?no)?)\b\s*([:=]|%3[daDA]))"
)


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
            page_token = None

            while True:
                request = self.admin_service.accountSummaries().list(
                    pageSize=200,
                    pageToken=page_token
                )
                response = request.execute()

                for account in response.get('accountSummaries', []):
                    account_name = account.get('displayName')
                    for propertySummary in account.get(
                        'propertySummaries',
                        []
                    ):
                        prop_path = propertySummary.get("property", "")
                        prop_id = (
                            prop_path.split("/")[1]
                            if "/" in prop_path
                            else prop_path
                        )
                        properties.append({
                            "id": prop_id,
                            "name": propertySummary.get(
                                "displayName"
                            ),
                            "account_name": account_name
                        })

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            # Sort alphabetically by account name, then property name
            properties.sort(
                key=lambda p: (
                    (p.get("account_name") or "").lower(),
                    (p.get("name") or "").lower()
                )
            )
            return properties

        except Exception as e:
            print(f"Failed to fetch properties: {e}")
            return []

    def get_all_custom_dimensions(self, property_id):
        try:
            custom_dims = []
            page_token = None

            while True:
                response = (
                    self.admin_service
                    .properties()
                    .customDimensions()
                    .list(
                        parent=f"properties/{property_id}",
                        pageSize=200,
                        pageToken=page_token
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

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

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

        # In GA4 Data API, querying dimensions with an empty metrics list returns
        # all unique dimension values without encountering scope incompatibility errors
        # (such as eventCount being incompatible with customItem or item-scoped dimensions).
        metrics = []

        all_leaks = []
        seen_leaks = set()

        # GA4 Data API pagination size
        page_size = 10000

        for dim in dimensions:

            offset = 0
            use_filter = True

            try:

                while True:

                    dimension_filter = None
                    if use_filter:
                        dimension_filter = FilterExpression(
                            filter=Filter(
                                field_name=dim,
                                string_filter=Filter.StringFilter(
                                    match_type=Filter.StringFilter.MatchType.PARTIAL_REGEXP,
                                    value=GA4_PII_CANDIDATE_REGEX,
                                    case_sensitive=False,
                                ),
                            )
                        )

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

                        dimension_filter=dimension_filter,

                        # Explicit pagination
                        limit=page_size,
                        offset=offset
                    )

                    try:
                        response = self.client.run_report(
                            request
                        )
                    except Exception as report_err:
                        # If dimension_filter is unsupported on this specific dimension, fall back to unfiltered scan
                        if use_filter and "filter" in str(report_err).lower():
                            print(
                                f"Dimension filter unsupported on '{dim}', "
                                f"falling back to full scan: {report_err}"
                            )
                            use_filter = False
                            offset = 0
                            continue
                        raise report_err

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
                        f"filtered={use_filter} | "
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

                # If the dimension is incompatible or causes an API error, skip it
                # gracefully so the audit can complete for all other valid dimensions
                print(
                    f"Warning: Skipping dimension '{dim}' for property "
                    f"{property_id} due to query error: {e}"
                )
                continue

        print(
            f"GA4 property {property_id} "
            f"produced {len(all_leaks)} "
            f"unique PII leak(s)"
        )

        return all_leaks