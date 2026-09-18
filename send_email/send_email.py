import os
import requests
from msal import ConfidentialClientApplication
from datetime import datetime
from zoneinfo import ZoneInfo


def utc_to_ist(utc_datetime_str):
    if not utc_datetime_str:
        return ""

    try:
        utc_dt = datetime.fromisoformat(
            utc_datetime_str.replace("Z", "+00:00")
        )

        ist_dt = utc_dt.astimezone(
            ZoneInfo("Asia/Kolkata")
        )

        return ist_dt.strftime("%d-%m-%Y %I:%M:%S %p IST")

    except Exception as e:
        print(f"Date conversion error: {e}")
        return utc_datetime_str


def get_access_token():
    """
    Generate Microsoft Graph access token
    """

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret
    )

    token_response = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )

    access_token = token_response.get("access_token")

    if not access_token:
        raise Exception(
            f"Token Error: {token_response}"
        )

    return access_token


def build_recipients(email_string):
    """
    Convert comma/semicolon separated emails
    into Graph API recipient format
    """

    if not email_string:
        return []

    email_string = email_string.replace(";", ",")

    emails = [
        email.strip()
        for email in email_string.split(",")
        if email.strip()
    ]

    return [
        {
            "emailAddress": {
                "address": email
            }
        }
        for email in emails
    ]


def send_email_notification(data):
    try:
        mail_cc = data.get("mail_cc")
        sender_email = data.get("sender_email")
        mail_to = data.get("mail_to")

        if not sender_email:
            raise ValueError("SENDER_EMAIL not found in .env.aa")

        if not mail_to:
            raise ValueError(
                "Receiver email was not provided in email_data "
                "and RECEIVER_EMAIL was not found in .env.aa"
            )
        access_token = get_access_token()

        activity_rows = ""
        for item in data.get("activities", []):
            status = str(item.get("status", "")).strip()
            if status.upper() == "RUN_FAILED":
                status_html = (
                    f'<span class="status-failed">{status}</span>'
                )
            elif status.upper() == "SUCCESS":
                status_html = (
                    f'<span class="status-success">{status}</span>'
                )
            else:
                status_html = (
                    f'<span class="status-warning">{status}</span>'
                )
            activity_rows += f"""
            <tr>
                <td data-label="Bot Name">
                    {item.get("fileName", "")}
                </td>

                <td data-label="Runner Name">
                    {item.get("userName", "")}
                </td>

                <td data-label="Status">
                    {status_html}
                </td>

                <td data-label="Type">
                    {item.get("type", "")}
                </td>

                <td data-label="End Time (IST)">
                    {utc_to_ist(item.get("endDateTime"))}
                </td>

                <td data-label="Error Message">
                    {item.get("message", "")}
                </td>
            </tr>
            """

        email_title = data.get(
            "email_title",
            "Automation Anywhere Monitoring Alert"
        )

        environment_name = data.get(
            "environment_name",
            "Production"
        )

        intro_message = data.get(
            "intro_message",
            "Exception activities were detected during the latest monitoring cycle."
        )

        action_message = data.get(
            "action_message",
            "Kindly investigate the failed executions and perform "
            "the required corrective actions."
        )

        total_count = data.get(
            "total_count",
            len(data.get("activities", []))
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <style>

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0 !important;
            padding: 0 !important;
            background-color: #f4f6f9;
            font-family: "Segoe UI", Arial, sans-serif;
            -webkit-text-size-adjust: 100%;
            width: 100% !important;
        }}

        .container {{
            width: 95%;
            max-width: 1200px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
        }}

        .header {{
            background-color: #003366;
            color: #ffffff;
            text-align: center;
            padding: 20px;
        }}

        .header h2 {{
            margin: 0;
            font-size: 24px;
            line-height: 32px;
        }}

        .content {{
            padding: 25px;
            color: #333333;
            font-size: 14px;
            line-height: 1.5;
        }}

        .alert-box {{
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}

        .summary {{
            background-color: #eef6ff;
            border: 1px solid #cfe2ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}

        .summary-title {{
            color: #003366;
            font-size: 16px;
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            font-size: 13px;
        }}

        th {{
            background-color: #003366;
            color: #ffffff;
            padding: 10px;
            text-align: left;
            border: 1px solid #dddddd;
        }}

        td {{
            border: 1px solid #dddddd;
            padding: 8px;
            vertical-align: top;
            overflow-wrap: anywhere;
            word-break: break-word;
        }}

        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}

        .status-success {{
            color: #198754;
            font-weight: bold;
        }}

        .status-warning {{
            color: #fd7e14;
            font-weight: bold;
        }}

        .footer {{
            padding: 15px 25px;
            background-color: #f8f9fa;
            color: #666666;
            font-size: 12px;
            border-top: 1px solid #dddddd;
        }}


        /* ============================= */
        /* MOBILE RESPONSIVE */
        /* ============================= */

        @media only screen and (max-width: 600px) {{

            body {{
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }}

            .container {{
                width: 100% !important;
                margin: 0 !important;
                border-radius: 0 !important;
            }}

            .header {{
                padding: 15px !important;
            }}

            .header h2 {{
                font-size: 19px !important;
                line-height: 25px !important;
            }}

            .content {{
                padding: 15px !important;
                font-size: 14px !important;
            }}

            .alert-box {{
                padding: 12px !important;
            }}

            .summary {{
                padding: 12px !important;
            }}

            /*
               Convert normal table to card layout.
               This avoids horizontal scrolling.
            */

            table,
            thead,
            tbody,
            th,
            td,
            tr {{
                display: block !important;
                width: 100% !important;
            }}

            thead {{
                display: none !important;
            }}

            table {{
                border: none !important;
            }}

            tbody tr {{
                background-color: #ffffff !important;
                border: 1px solid #dddddd !important;
                border-radius: 8px !important;
                margin-bottom: 15px !important;
                overflow: hidden !important;
            }}

            td {{
                display: block !important;
                width: 100% !important;
                padding: 10px !important;
                border: none !important;
                border-bottom: 1px solid #eeeeee !important;
                overflow-wrap: anywhere !important;
                word-break: break-word !important;
            }}

            td:last-child {{
                border-bottom: none !important;
            }}

            td::before {{
                content: attr(data-label);
                display: block;
                color: #003366;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 4px;
            }}

            .footer {{
                padding: 15px !important;
                font-size: 11px !important;
            }}
        }}

        </style>
        </head>

        <body>

        <div class="container">

            <div class="header">
                <h2>{email_title}</h2>
            </div>

            <div class="content">

                <p>Hello Team,</p>

                <p>
                    This is an automated notification generated by the
                    <strong>Automation Anywhere Monitoring System</strong>.
                </p>

                <div class="alert-box">

                    <strong>Attention Required</strong>
                    <br><br>

                    {intro_message}

                    <br><br>

                    Total exception activities:
                    <strong>{total_count}</strong>

                </div>

                <div class="summary">

                    <div class="summary-title">
                        Monitoring Summary
                    </div>

                    <br>

                    Environment:
                    <strong>{environment_name}</strong>

                    <br>

                    Total Exception Activities:
                    <strong>{total_count}</strong>

                    <br>

                    Report Generated:
                    <strong>
                        {
        datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime(
            "%d-%m-%Y %I:%M %p IST"
        )
        }
                    </strong>

                </div>

                <h3 style="color:#003366;">
                    Failed Activity Details
                </h3>

                <table role="presentation">

                    <thead>
                        <tr>
                            <th>Bot Name</th>
                            <th>Runner Name</th>
                            <th>Status</th>
                            <th>Type</th>
                            <th>End Time (IST)</th>
                            <th>Error Message</th>
                        </tr>
                    </thead>

                    <tbody>
                        {activity_rows}
                    </tbody>

                </table>

                <br>

                <p>
                    {action_message}
                </p>

                <p>
                    Regards,
                    <br>
                    <strong>
                        Automation Monitoring System
                    </strong>
                </p>

            </div>

            <div class="footer">
                This is a system-generated email.
                Please do not reply to this mailbox.
            </div>

        </div>

        </body>
        </html>
        """

        email_payload = {
            "message": {
                "subject": data.get("subject",""),
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "toRecipients": build_recipients(mail_to)
            },
            "saveToSentItems": True
        }

        cc_recipients = build_recipients(mail_cc)

        if cc_recipients:
            email_payload["message"]["ccRecipients"] = cc_recipients

        url = (
            f"https://graph.microsoft.com/v1.0/"
            f"users/{sender_email}/sendMail"
        )

        response = requests.post(
            url,
            headers={
                "Authorization":
                    f"Bearer {access_token}",
                "Content-Type":
                    "application/json"
            },
            json=email_payload,
            timeout=60
        )

        print("=" * 60)
        print("Status Code :", response.status_code)
        print("Response    :", response.text)
        print("=" * 60)

        if response.status_code == 202:
            print("✅ Email Sent Successfully")
            return True

        print("❌ Email Sending Failed")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False
