import os
import html
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from msal import ConfidentialClientApplication


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# If .env.aa is in the project root and send_email is a subfolder
PROJECT_ROOT = BASE_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env.aa"

load_dotenv(ENV_FILE)

IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_html(value):
    """
    Convert a value into an HTML-safe string.
    """

    if value is None:
        return ""

    return html.escape(
        str(value).strip()
    )


def utc_to_ist(utc_datetime_value):
    """
    Convert an Automation Anywhere UTC datetime value to IST.

    Example input:
        2026-09-18T08:30:00Z

    Example output:
        18-09-2026 02:00:00 PM IST
    """

    if not utc_datetime_value:
        return ""

    try:
        datetime_string = str(
            utc_datetime_value
        ).strip()

        utc_datetime = datetime.fromisoformat(
            datetime_string.replace(
                "Z",
                "+00:00"
            )
        )

        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(
                tzinfo=ZoneInfo("UTC")
            )

        ist_datetime = utc_datetime.astimezone(
            IST
        )

        return ist_datetime.strftime(
            "%d-%m-%Y %I:%M:%S %p IST"
        )

    except (ValueError, TypeError) as error:
        print(
            f"Date conversion error: "
            f"{utc_datetime_value} | {error}"
        )

        return str(utc_datetime_value)


# ============================================================
# MICROSOFT GRAPH TOKEN
# ============================================================

def get_access_token():
    """
    Generate a Microsoft Graph application access token.
    """

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    missing_variables = []

    if not tenant_id:
        missing_variables.append("TENANT_ID")

    if not client_id:
        missing_variables.append("CLIENT_ID")

    if not client_secret:
        missing_variables.append("CLIENT_SECRET")

    if missing_variables:
        raise ValueError(
            "Missing environment variables: "
            + ", ".join(missing_variables)
        )

    authority = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}"
    )

    application = ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret
    )

    token_response = application.acquire_token_for_client(
        scopes=[
            "https://graph.microsoft.com/.default"
        ]
    )

    access_token = token_response.get(
        "access_token"
    )

    if not access_token:
        error_description = token_response.get(
            "error_description",
            str(token_response)
        )

        raise RuntimeError(
            f"Microsoft Graph token error: "
            f"{error_description}"
        )

    return access_token


# ============================================================
# RECIPIENT BUILDER
# ============================================================

def build_recipients(email_value):
    """
    Convert email addresses into Microsoft Graph format.

    Supported values:
        user1@company.com,user2@company.com
        user1@company.com;user2@company.com
        ["user1@company.com", "user2@company.com"]
    """

    if not email_value:
        return []

    if isinstance(email_value, (list, tuple, set)):
        email_list = email_value

    else:
        email_list = str(
            email_value
        ).replace(
            ";",
            ","
        ).split(",")

    unique_emails = []
    seen_emails = set()

    for email_address in email_list:

        clean_email = str(
            email_address
        ).strip()

        if not clean_email:
            continue

        normalized_email = clean_email.lower()

        if normalized_email in seen_emails:
            continue

        seen_emails.add(
            normalized_email
        )

        unique_emails.append(
            clean_email
        )

    return [
        {
            "emailAddress": {
                "address": email_address
            }
        }
        for email_address in unique_emails
    ]


# ============================================================
# STATUS FORMATTING
# ============================================================

def get_status_html(status):
    """
    Generate executive-friendly HTML status badge.
    """

    clean_status = str(
        status or "UNKNOWN"
    ).strip().upper()

    status_mapping = {
        "RUN_FAILED": (
            "Failed",
            "status-failed"
        ),
        "DEPLOY_FAILED": (
            "Deploy Failed",
            "status-failed"
        ),
        "RUN_ABORTED": (
            "Aborted",
            "status-failed"
        ),
        "RUN_TIMED_OUT": (
            "Timed Out",
            "status-failed"
        ),
        "COMPLETED": (
            "Completed",
            "status-completed"
        ),
        "SUCCESS": (
            "Completed",
            "status-completed"
        ),
        "RUN_COMPLETED": (
            "Completed",
            "status-completed"
        )
    }

    display_status, status_class = status_mapping.get(
        clean_status,
        (
            clean_status.replace("_", " ").title(),
            "status-other"
        )
    )

    return (
        f'<span class="status {status_class}">'
        f'{safe_html(display_status)}'
        f'</span>'
    )


# ============================================================
# ACTIVITY TABLE ROWS
# ============================================================

def build_activity_rows(
    activities,
    section_type
):
    """
    Build activity rows.

    Failed section:
        #, Bot Name, Runner, Status, Completion Time, Details

    Completed section:
        #, Bot Name, Runner, Status, Completion Time
    """

    rows = []

    for serial_number, activity in enumerate(
        activities or [],
        start=1
    ):
        if not isinstance(activity, dict):
            continue

        bot_name = safe_html(
            activity.get(
                "fileName",
                activity.get(
                    "automationName",
                    ""
                )
            )
        ) or "Not available"

        runner_name = safe_html(
            activity.get(
                "userName",
                ""
            )
        ) or "Not available"

        status_html = get_status_html(
            activity.get(
                "status",
                ""
            )
        )

        completion_time = safe_html(
            utc_to_ist(
                activity.get(
                    "endDateTime"
                )
            )
        ) or "Not available"

        # Common columns
        row_html = f"""
        <tr>
            <td
                class="number-cell"
                data-label="No."
            >
                {serial_number}
            </td>

            <td
                class="bot-name-cell"
                data-label="Bot Name"
            >
                <strong>{bot_name}</strong>
            </td>

            <td data-label="Runner">
                {runner_name}
            </td>

            <td data-label="Status">
                {status_html}
            </td>

            <td data-label="Completion Time">
                {completion_time}
            </td>
        """

        # Details column only for failed activities
        if section_type == "failed":
            error_message = safe_html(
                activity.get(
                    "message",
                    ""
                )
            ) or "No exception details available"

            row_html += f"""
            <td
                class="message-cell"
                data-label="Details"
            >
                {error_message}
            </td>
            """

        row_html += """
        </tr>
        """

        rows.append(row_html)

    return "".join(rows)


# ============================================================
# ACTIVITY SECTION
# ============================================================

def build_activity_section(
    title,
    activities,
    section_type
):
    """
    Build an executive-level activity section.

    Failed activity columns:
        #, Bot Name, Runner, Status, Completion Time, Details

    Completed activity columns:
        #, Bot Name, Runner, Status, Completion Time

    Args:
        title:
            Section heading displayed in the email.

        activities:
            List of activity dictionaries.

        section_type:
            Either "failed" or "completed".

    Returns:
        HTML string for the complete activity section.
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    activities = activities or []

    if not isinstance(activities, list):
        activities = []

    section_type = str(
        section_type or ""
    ).strip().lower()

    if section_type not in {
        "failed",
        "completed"
    }:
        raise ValueError(
            "section_type must be either "
            "'failed' or 'completed'."
        )

    activity_count = len(activities)

    # ========================================================
    # SECTION CONFIGURATION
    # ========================================================

    if section_type == "failed":

        title_class = "failed-section-title"
        count_class = "failed-count"

        section_description = (
            "Bot executions requiring review or "
            "corrective action."
        )

        empty_message = (
            "No exceptions were identified during "
            "the reporting period."
        )

        # Failed section includes the Details column
        column_group = """
        <colgroup>
            <col style="width: 5%;">
            <col style="width: 22%;">
            <col style="width: 12%;">
            <col style="width: 12%;">
            <col style="width: 19%;">
            <col style="width: 30%;">
        </colgroup>
        """

        table_headers = """
        <tr>
            <th class="number-header">
                #
            </th>

            <th>
                Bot Name
            </th>

            <th>
                Runner
            </th>

            <th>
                Status
            </th>

            <th>
                Completion Time
            </th>

            <th>
                Details
            </th>
        </tr>
        """

    else:

        title_class = "completed-section-title"
        count_class = "completed-count"

        section_description = (
            "Bot executions completed successfully "
            "during the reporting period."
        )

        empty_message = (
            "No completed executions were recorded "
            "during the reporting period."
        )

        # Completed section does not include Details
        column_group = """
        <colgroup>
            <col style="width: 6%;">
            <col style="width: 34%;">
            <col style="width: 18%;">
            <col style="width: 16%;">
            <col style="width: 26%;">
        </colgroup>
        """

        table_headers = """
        <tr>
            <th class="number-header">
                #
            </th>

            <th>
                Bot Name
            </th>

            <th>
                Runner
            </th>

            <th>
                Status
            </th>

            <th>
                Completion Time
            </th>
        </tr>
        """

    # ========================================================
    # EMPTY ACTIVITY SECTION
    # ========================================================

    if not activities:

        return f"""
        <div class="activity-section">

            <div class="section-heading {title_class}">

                <span class="section-heading-text">
                    {safe_html(title)}
                </span>

                <span class="section-count {count_class}">
                    0
                </span>

            </div>

            <div class="section-description">
                {safe_html(section_description)}
            </div>

            <div class="empty-message">
                {safe_html(empty_message)}
            </div>

        </div>
        """

    # ========================================================
    # BUILD ACTIVITY ROWS
    # ========================================================

    activity_rows = build_activity_rows(
        activities=activities,
        section_type=section_type
    )

    # If activities were present but no valid dictionary rows
    # were generated
    if not activity_rows.strip():

        return f"""
        <div class="activity-section">

            <div class="section-heading {title_class}">

                <span class="section-heading-text">
                    {safe_html(title)}
                </span>

                <span class="section-count {count_class}">
                    0
                </span>

            </div>

            <div class="section-description">
                {safe_html(section_description)}
            </div>

            <div class="empty-message">
                No valid activity records were available.
            </div>

        </div>
        """

    # ========================================================
    # COMPLETE ACTIVITY TABLE
    # ========================================================

    return f"""
    <div class="activity-section">

        <div class="section-heading {title_class}">

            <span class="section-heading-text">
                {safe_html(title)}
            </span>

            <span class="section-count {count_class}">
                {activity_count}
            </span>

        </div>

        <div class="section-description">
            {safe_html(section_description)}
        </div>

        <table
            class="activity-table"
            role="table"
            cellpadding="0"
            cellspacing="0"
            border="0"
        >

            {column_group}

            <thead>
                {table_headers}
            </thead>

            <tbody>
                {activity_rows}
            </tbody>

        </table>

    </div>
    """

# ============================================================
# BUILD EMAIL HTML
# ============================================================

def build_email_html(data):
    """
    Build an executive-level Automation Anywhere
    daily bot execution monitoring report.
    """

    # ========================================================
    # DATA
    # ========================================================

    failed_activities = data.get(
        "failed_activities",
        []
    ) or []

    completed_activities = data.get(
        "completed_activities",
        []
    ) or []

    failed_count = data.get(
        "failed_count",
        len(failed_activities)
    )

    completed_count = data.get(
        "completed_count",
        len(completed_activities)
    )

    total_count = data.get(
        "total_count",
        failed_count + completed_count
    )

    # ========================================================
    # SUCCESS RATE
    # ========================================================

    if total_count > 0:
        success_rate = (
            completed_count / total_count
        ) * 100
    else:
        success_rate = 0

    success_rate_text = f"{success_rate:.1f}%"

    # ========================================================
    # EMAIL DETAILS
    # ========================================================

    email_title = safe_html(
        data.get(
            "email_title",
            "Automation Anywhere Executive Monitoring Report"
        )
    )

    environment_name = safe_html(
        data.get(
            "environment_name",
            "Production"
        )
    )

    report_start_time = safe_html(
        data.get(
            "report_start_time",
            "Yesterday 07:00 PM IST"
        )
    )

    report_end_time = safe_html(
        data.get(
            "report_end_time",
            "Current Time"
        )
    )

    generated_time = datetime.now(
        IST
    ).strftime(
        "%d-%m-%Y %I:%M %p IST"
    )

    # ========================================================
    # EXECUTIVE HEALTH STATUS
    # ========================================================

    if failed_count == 0:

        health_status = "HEALTHY"
        health_text = (
            "All monitored bot executions completed successfully "
            "during the reporting period."
        )

        health_background = "#ECFDF3"
        health_border = "#12B76A"
        health_color = "#027A48"

        action_title = "No Immediate Action Required"

        action_message = (
            "The monitored automation environment is operating "
            "normally. Continue standard operational monitoring."
        )

    elif success_rate >= 90:

        health_status = "ATTENTION REQUIRED"

        health_text = (
            f"{failed_count} exception(s) were identified while "
            f"maintaining an overall success rate of "
            f"{success_rate_text}."
        )

        health_background = "#FFFAEB"
        health_border = "#F79009"
        health_color = "#B54708"

        action_title = "Review Required"

        action_message = (
            "Please review the exception details below and ensure "
            "appropriate corrective actions are taken."
        )

    else:

        health_status = "CRITICAL ATTENTION"

        health_text = (
            f"{failed_count} failed execution(s) were identified. "
            f"The overall success rate is {success_rate_text}."
        )

        health_background = "#FEF3F2"
        health_border = "#F04438"
        health_color = "#B42318"

        action_title = "Immediate Attention Required"

        action_message = (
            "Please prioritize the failed executions, identify "
            "the root causes, and initiate corrective actions."
        )

    # ========================================================
    # ACTIVITY SECTIONS
    # ========================================================

    failed_section = build_activity_section(
        title="Exception Details",
        activities=failed_activities,
        section_type="failed"
    )

    completed_section = build_activity_section(
        title="Successful Execution Details",
        activities=completed_activities,
        section_type="completed"
    )

    # ========================================================
    # HTML
    # ========================================================

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>{email_title}</title>

<style>
.section-description {{
    margin: -3px 0 10px;
    color: #667085;
    font-size: 11px;
    line-height: 17px;
}}

.number-cell {{
    color: #667085 !important;
    text-align: center !important;
}}

.bot-name-cell {{
    color: #101828 !important;
}}

.message-cell {{
    color: #475467 !important;
}}

* {{
    box-sizing: border-box;
}}

html,
body {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}}

body {{
    background-color: #F2F4F7;
    color: #344054;
    font-family: "Segoe UI", Arial, sans-serif;
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}}

table {{
    border-spacing: 0;
}}

.email-wrapper {{
    width: 100%;
    padding: 28px 10px;
    background-color: #F2F4F7;
}}

.email-container {{
    width: 96%;
    max-width: 1200px;
    margin: 0 auto;
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 10px;
    overflow: hidden;
}}


/* ===================================================== */
/* EXECUTIVE HEADER                                      */
/* ===================================================== */

.executive-header {{
    padding: 28px 32px;
    background-color: #002B49;
    color: #FFFFFF;
}}

.header-label {{
    margin-bottom: 7px;
    color: #9FC3DC;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}

.header-title {{
    margin: 0;
    color: #FFFFFF;
    font-size: 25px;
    font-weight: 600;
    line-height: 32px;
}}

.header-meta {{
    margin-top: 8px;
    color: #D0E2EF;
    font-size: 13px;
}}


/* ===================================================== */
/* CONTENT                                               */
/* ===================================================== */

.content {{
    padding: 30px 32px;
    font-size: 14px;
    line-height: 1.6;
}}

.intro {{
    margin: 0 0 22px;
    color: #475467;
}}


/* ===================================================== */
/* EXECUTIVE HEALTH                                      */
/* ===================================================== */

.health-card {{
    margin-bottom: 28px;
    padding: 17px 20px;
    background-color: {health_background};
    border: 1px solid {health_border};
    border-left: 5px solid {health_border};
    border-radius: 6px;
}}

.health-label {{
    margin-bottom: 4px;
    color: #667085;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

.health-status {{
    margin-bottom: 5px;
    color: {health_color};
    font-size: 17px;
    font-weight: 700;
}}

.health-description {{
    color: #475467;
    font-size: 13px;
    line-height: 20px;
}}


/* ===================================================== */
/* SECTION TITLE                                         */
/* ===================================================== */

.dashboard-title {{
    margin: 0 0 12px;
    color: #101828;
    font-size: 17px;
    font-weight: 600;
}}


/* ===================================================== */
/* KPI CARDS                                             */
/* ===================================================== */

.kpi-table {{
    width: 100%;
    margin: 0 0 26px;
    border-collapse: separate;
    border-spacing: 7px;
    table-layout: fixed;
}}

.kpi-card {{
    padding: 17px 12px;
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 7px;
    vertical-align: middle;
}}

.kpi-label {{
    margin-bottom: 5px;
    color: #667085;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

.kpi-value {{
    color: #101828;
    font-size: 25px;
    font-weight: 700;
    line-height: 31px;
}}

.kpi-value.total {{
    color: #175CD3;
}}

.kpi-value.completed {{
    color: #027A48;
}}

.kpi-value.failed {{
    color: #B42318;
}}

.kpi-value.rate {{
    color: #003366;
}}

.kpi-subtitle {{
    margin-top: 3px;
    color: #98A2B3;
    font-size: 10px;
}}


/* ===================================================== */
/* REPORT INFORMATION                                    */
/* ===================================================== */

.report-info {{
    margin-bottom: 30px;
    padding: 16px 18px;
    background-color: #F8FAFC;
    border: 1px solid #E4E7EC;
    border-radius: 6px;
}}

.report-info-title {{
    margin-bottom: 9px;
    color: #344054;
    font-size: 13px;
    font-weight: 700;
}}

.report-info-table {{
    width: 100%;
    border-collapse: collapse;
}}

.report-info-table td {{
    padding: 3px 8px 3px 0;
    border: none;
    font-size: 12px;
    line-height: 18px;
}}

.report-label {{
    color: #667085;
    font-weight: 600;
}}

.report-value {{
    color: #344054;
}}


/* ===================================================== */
/* ACTIVITY SECTION                                      */
/* ===================================================== */

.activity-section {{
    margin-top: 30px;
    margin-bottom: 32px;
}}

.section-heading {{
    margin-bottom: 11px;
    padding: 11px 14px;
    border-radius: 5px;
    font-size: 15px;
    font-weight: 700;
}}

.failed-section-title {{
    background-color: #FEF3F2;
    border-left: 4px solid #D92D20;
    color: #B42318;
}}

.completed-section-title {{
    background-color: #ECFDF3;
    border-left: 4px solid #12B76A;
    color: #067647;
}}

.section-count {{
    float: right;
    min-width: 26px;
    padding: 2px 8px;
    border-radius: 12px;
    color: #FFFFFF;
    font-size: 11px;
    text-align: center;
}}

.failed-count {{
    background-color: #D92D20;
}}

.completed-count {{
    background-color: #039855;
}}


/* ===================================================== */
/* ACTIVITY TABLE                                        */
/* ===================================================== */

.activity-table {{
    width: 100%;
    border-collapse: collapse !important;
    table-layout: fixed;
    border: 1px solid #98a2b3 !important;
    font-size: 11px;
}}

.activity-table th {{
    padding: 11px 9px;
    background-color: #344054;
    border: 1px solid #667085 !important;
    color: #ffffff;
    font-size: 10px;
    font-weight: 700;
    line-height: 16px;
    text-align: left;
    text-transform: uppercase;
    vertical-align: middle;
}}

.activity-table td {{
    padding: 10px 9px;
    background-color: #ffffff;
    border: 1px solid #cfd4dc !important;
    color: #344054;
    font-size: 11px;
    line-height: 17px;
    text-align: left;
    vertical-align: top;
    overflow-wrap: anywhere;
    word-break: break-word;
}}

.activity-table tbody tr:nth-child(even) td {{
    background-color: #f8fafc;
}}

.number-header,
.number-cell {{
    text-align: center !important;
}}

.bot-name-cell {{
    color: #101828 !important;
}}

.message-cell {{
    color: #475467 !important;
}}


/* ===================================================== */
/* STATUS BADGES                                         */
/* ===================================================== */

.status {{
    display: inline-block;
    padding: 3px 7px;
    border-radius: 12px;
    font-size: 9px;
    font-weight: 700;
    white-space: nowrap;
}}

.status-failed {{
    background-color: #FEE4E2;
    color: #B42318;
}}

.status-completed {{
    background-color: #D1FADF;
    color: #05603A;
}}

.status-other {{
    background-color: #FEF0C7;
    color: #93370D;
}}


/* ===================================================== */
/* EMPTY MESSAGE                                         */
/* ===================================================== */

.empty-message {{
    padding: 16px;
    background-color: #F9FAFB;
    border: 1px solid #EAECF0;
    border-radius: 5px;
    color: #667085;
    font-size: 12px;
    text-align: center;
}}


/* ===================================================== */
/* MANAGEMENT ACTION                                     */
/* ===================================================== */

.management-action {{
    margin-top: 30px;
    padding: 17px 18px;
    background-color: #F8FAFC;
    border: 1px solid #E4E7EC;
    border-left: 4px solid #175CD3;
    border-radius: 5px;
}}

.action-title {{
    margin-bottom: 4px;
    color: #175CD3;
    font-size: 13px;
    font-weight: 700;
}}

.action-description {{
    color: #475467;
    font-size: 12px;
    line-height: 19px;
}}


/* ===================================================== */
/* SIGNATURE                                             */
/* ===================================================== */

.signature {{
    margin-top: 24px;
    color: #475467;
    font-size: 13px;
}}

.signature-name {{
    color: #344054;
    font-weight: 600;
}}


/* ===================================================== */
/* FOOTER                                                */
/* ===================================================== */

.footer {{
    padding: 17px 30px;
    background-color: #F9FAFB;
    border-top: 1px solid #EAECF0;
    color: #98A2B3;
    font-size: 10px;
    line-height: 16px;
    text-align: center;
}}


/* ===================================================== */
/* MOBILE                                                */
/* ===================================================== */

@media only screen and (max-width: 650px) {{

    .email-wrapper {{
        padding: 0 !important;
    }}

    .email-container {{
        width: 100% !important;
        border: none !important;
        border-radius: 0 !important;
    }}

    .executive-header {{
        padding: 20px 16px !important;
    }}

    .header-title {{
        font-size: 20px !important;
        line-height: 26px !important;
    }}

    .content {{
        padding: 20px 14px !important;
    }}

    .health-card {{
        padding: 14px !important;
    }}

    /* KPI CARDS */

    .kpi-table,
    .kpi-table tbody,
    .kpi-table tr,
    .kpi-table td {{
        display: block !important;
        width: 100% !important;
    }}

    .kpi-table {{
        border-spacing: 0 !important;
    }}

    .kpi-card {{
        margin-bottom: 8px !important;
    }}

    /* REPORT INFO */

    .report-info-table,
    .report-info-table tbody,
    .report-info-table tr,
    .report-info-table td {{
        display: block !important;
        width: 100% !important;
    }}

    .report-label {{
        padding-top: 7px !important;
        padding-bottom: 0 !important;
        color: #98A2B3 !important;
        font-size: 9px !important;
        text-transform: uppercase;
    }}

    .report-value {{
        padding-top: 0 !important;
        padding-bottom: 4px !important;
    }}

    /* ACTIVITY CARDS */

    .activity-table,
    .activity-table tbody,
    .activity-table tr,
    .activity-table td {{
        display: block !important;
        width: 100% !important;
    }}

    .activity-table thead {{
        display: none !important;
    }}

    .activity-table {{
        border: none !important;
    }}

    .activity-table tbody tr {{
        margin-bottom: 14px !important;
        overflow: hidden !important;
        background-color: #FFFFFF !important;
        border: 1px solid #D0D5DD !important;
        border-radius: 6px !important;
    }}

    .activity-table td {{
        display: block !important;
        width: 100% !important;
        padding: 9px 11px !important;
        border: none !important;
        border-bottom: 1px solid #EAECF0 !important;
    }}

    .activity-table td:last-child {{
        border-bottom: none !important;
    }}

    .activity-table td::before {{
        content: attr(data-label);
        display: block;
        margin-bottom: 3px;
        color: #98A2B3;
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
    }}

    .management-action {{
        padding: 14px !important;
    }}

    .footer {{
        padding: 14px !important;
    }}
}}

</style>

</head>


<body>

<div class="email-wrapper">

<div class="email-container">


    <!-- ================================================= -->
    <!-- EXECUTIVE HEADER                                  -->
    <!-- ================================================= -->

    <div class="executive-header">

        <div class="header-label">
            Daily Automation Operations
        </div>

        <div class="header-title">
            {email_title}
        </div>

        <div class="header-meta">
            {environment_name} Environment
            &nbsp;&nbsp;|&nbsp;&nbsp;
            {generated_time}
        </div>

    </div>


    <div class="content">


        <!-- ================================================= -->
        <!-- INTRODUCTION                                      -->
        <!-- ================================================= -->

        <p class="intro">

            Hello Team,
            <br><br>

            Please find below the executive summary of
            Automation Anywhere bot execution performance
            for the latest monitoring period.

        </p>


        <!-- ================================================= -->
        <!-- EXECUTIVE HEALTH                                  -->
        <!-- ================================================= -->

        <div class="health-card">

            <div class="health-label">
                Overall Automation Health
            </div>

            <div class="health-status">
                {health_status}
            </div>

            <div class="health-description">
                {health_text}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- KPI SUMMARY                                       -->
        <!-- ================================================= -->

        <div class="dashboard-title">
            Performance Snapshot
        </div>


        <table
            class="kpi-table"
            role="presentation"
            cellpadding="0"
            cellspacing="0"
        >

            <tbody>

            <tr>

                <td class="kpi-card">

                    <div class="kpi-label">
                        Total Executions
                    </div>

                    <div class="kpi-value total">
                        {total_count}
                    </div>

                    <div class="kpi-subtitle">
                        Monitored executions
                    </div>

                </td>


                <td class="kpi-card">

                    <div class="kpi-label">
                        Successful
                    </div>

                    <div class="kpi-value completed">
                        {completed_count}
                    </div>

                    <div class="kpi-subtitle">
                        Completed executions
                    </div>

                </td>


                <td class="kpi-card">

                    <div class="kpi-label">
                        Exceptions
                    </div>

                    <div class="kpi-value failed">
                        {failed_count}
                    </div>

                    <div class="kpi-subtitle">
                        Requires review
                    </div>

                </td>


                <td class="kpi-card">

                    <div class="kpi-label">
                        Success Rate
                    </div>

                    <div class="kpi-value rate">
                        {success_rate_text}
                    </div>

                    <div class="kpi-subtitle">
                        Execution reliability
                    </div>

                </td>

            </tr>

            </tbody>

        </table>


        <!-- ================================================= -->
        <!-- REPORTING INFORMATION                             -->
        <!-- ================================================= -->

        <div class="report-info">

            <div class="report-info-title">
                Reporting Window
            </div>

            <table
                class="report-info-table"
                role="presentation"
                cellpadding="0"
                cellspacing="0"
            >

                <tbody>

                <tr>

                    <td class="report-label">
                        Period Start
                    </td>

                    <td class="report-value">
                        {report_start_time}
                    </td>

                    <td class="report-label">
                        Period End
                    </td>

                    <td class="report-value">
                        {report_end_time}
                    </td>

                </tr>

                <tr>

                    <td class="report-label">
                        Environment
                    </td>

                    <td class="report-value">
                        {environment_name}
                    </td>

                    <td class="report-label">
                        Generated
                    </td>

                    <td class="report-value">
                        {generated_time}
                    </td>

                </tr>

                </tbody>

            </table>

        </div>


        <!-- ================================================= -->
        <!-- EXCEPTIONS FIRST                                  -->
        <!-- ================================================= -->

        {failed_section}


        <!-- ================================================= -->
        <!-- SUCCESSFUL EXECUTIONS                              -->
        <!-- ================================================= -->

        {completed_section}


        <!-- ================================================= -->
        <!-- MANAGEMENT ACTION                                 -->
        <!-- ================================================= -->

        <div class="management-action">

            <div class="action-title">
                {action_title}
            </div>

            <div class="action-description">
                {action_message}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- SIGNATURE                                         -->
        <!-- ================================================= -->

        <div class="signature">

            Regards,
            <br>

            <span class="signature-name">
                Automation Monitoring System
            </span>

        </div>


    </div>


    <!-- ================================================= -->
    <!-- FOOTER                                            -->
    <!-- ================================================= -->

    <div class="footer">

        This report is automatically generated by the
        Automation Monitoring System for operational visibility.
        Please do not reply to this email.

    </div>


</div>

</div>

</body>

</html>
"""


# ============================================================
# SEND MORNING EMAIL
# ============================================================

def send_email_notification_morning(data):
    """
    Send the Automation Anywhere morning report using
    Microsoft Graph API.

    Required data structure:

        {
            "subject": "...",
            "email_title": "...",
            "environment_name": "Production",
            "report_start_time": "...",
            "report_end_time": "...",
            "failed_activities": [],
            "completed_activities": [],
            "failed_count": 0,
            "completed_count": 0,
            "total_count": 0,
            "mail_to": "...",
            "mail_cc": "..."
        }
    """

    try:

        if not isinstance(data, dict):
            raise TypeError(
                "Email data must be a dictionary."
            )

        # ----------------------------------------------------
        # SENDER
        # ----------------------------------------------------

        sender_email = (
            data.get("sender_email")
            or os.getenv("SENDER_EMAIL")
        )

        if not sender_email:
            raise ValueError(
                "SENDER_EMAIL was not provided and was not "
                "found in .env.aa."
            )

        # ----------------------------------------------------
        # RECIPIENTS
        # ----------------------------------------------------

        mail_to = (
            data.get("mail_to")
            or os.getenv("RECEIVER_EMAIL")
        )

        mail_cc = (
            data.get("mail_cc")
            or os.getenv("CC_EMAIL", "")
        )

        to_recipients = build_recipients(
            mail_to
        )

        cc_recipients = build_recipients(
            mail_cc
        )

        if not to_recipients:
            raise ValueError(
                "No valid To recipient was provided."
            )

        # ----------------------------------------------------
        # EMAIL SUBJECT
        # ----------------------------------------------------

        subject = str(
            data.get(
                "subject",
                "AA Production Bot Execution Morning Report"
            )
        ).strip()

        # ----------------------------------------------------
        # BUILD HTML
        # ----------------------------------------------------

        html_content = build_email_html(
            data
        )

        # ----------------------------------------------------
        # GRAPH PAYLOAD
        # ----------------------------------------------------

        message = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_content
            },
            "toRecipients": to_recipients
        }

        if cc_recipients:
            message["ccRecipients"] = (
                cc_recipients
            )

        email_payload = {
            "message": message,
            "saveToSentItems": True
        }

        # ----------------------------------------------------
        # ACCESS TOKEN
        # ----------------------------------------------------

        access_token = get_access_token()

        # ----------------------------------------------------
        # GRAPH ENDPOINT
        # ----------------------------------------------------

        graph_url = (
            "https://graph.microsoft.com/v1.0/"
            f"users/{sender_email}/sendMail"
        )

        request_headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Content-Type": "application/json"
        }

        # ----------------------------------------------------
        # SEND EMAIL
        # ----------------------------------------------------

        response = requests.post(
            url=graph_url,
            headers=request_headers,
            json=email_payload,
            timeout=60
        )

        print("=" * 70)
        print("EMAIL NOTIFICATION RESULT")
        print("=" * 70)
        print("Subject     :", subject)
        print("Sender      :", sender_email)
        print("To          :", mail_to)
        print("CC          :", mail_cc)
        print("Status Code :", response.status_code)

        if response.text:
            print("Response    :", response.text)

        print("=" * 70)

        if response.status_code == 202:
            print(
                "Morning report email sent successfully."
            )
            return True

        print(
            "Morning report email could not be sent."
        )

        return False

    except requests.exceptions.Timeout:
        print(
            "Email notification failed because the "
            "Microsoft Graph request timed out."
        )

        return False

    except requests.exceptions.ConnectionError as error:
        print(
            f"Microsoft Graph connection error: {error}"
        )

        return False

    except requests.exceptions.RequestException as error:
        print(
            f"Microsoft Graph request error: {error}"
        )

        return False

    except Exception as error:
        print(
            f"Morning email notification error: {error}"
        )

        return False