import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from msal import ConfidentialClientApplication
from datetime import datetime
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent

env_file = BASE_DIR / ".env.aa"
template_file = BASE_DIR / "email_notification_template.html"




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

        load_dotenv(env_file)

        sender_email = os.getenv("SENDER_EMAIL")
        mail_to = os.getenv("RECEIVER_EMAIL")


        if not sender_email:
            raise Exception(
                "SENDER_EMAIL not found in .env.aa"
            )

        access_token = get_access_token()

        activity_rows = ""

        for item in data.get("activities", []):
            status = item.get("status", "")
            if status.upper() == "RUN_FAILED":
                status_html = f'<span class="status-failed">{status}</span>'
            elif status.upper() == "SUCCESS":
                status_html = f'<span class="status-success">{status}</span>'
            else:
                status_html = f'<span class="status-warning">{status}</span>'

            activity_rows += f"""
            <tr>
                <td>{item.get('fileName', '')}</td>
                <td>{item.get('userName', '')}</td>
                <td>{status_html}</td>
                <td>{item.get('type', '')}</td>
                <td>{utc_to_ist(item.get('endDateTime'))}</td>
                <td>{item.get('message', '')}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>

        <head>
        <meta charset="UTF-8">

        <style>

        body {{
            margin: 0;
            padding: 0;
            background-color: #f4f6f9;
            font-family: Segoe UI, Arial, sans-serif;
        }}

        .container {{
            width: 95%;
            max-width: 1200px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0px 3px 10px rgba(0,0,0,0.1);
        }}

        .header {{
            background: #003366;
            color: white;
            text-align: center;
            padding: 20px;
        }}

        .header h2 {{
            margin: 0;
            font-size: 24px;
        }}

        .content {{
            padding: 25px;
            color: #333333;
            font-size: 14px;
        }}

        .alert-box {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}

        .summary {{
            background: #eef6ff;
            border: 1px solid #cfe2ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}

        .summary strong {{
            color: #003366;
            font-size: 16px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        th {{
            background: #003366;
            color: white;
            padding: 10px;
            text-align: left;
        }}

        td {{
            border: 1px solid #dddddd;
            padding: 8px;
            vertical-align: top;
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
            background: #f8f9fa;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #ddd;
        }}

        </style>

        </head>

        <body>

        <div class="container">

            <div class="header">
                <h2>Automation Anywhere Monitoring Alert</h2>
            </div>

            <div class="content">

                <p>Hello Team,</p>

                <p>
                    This is an automated notification generated by the
                    <strong>Automation Anywhere Monitoring System</strong>.
                </p>

                <div class="alert-box">
                    <strong>Attention Required</strong><br>
                    A total of <strong>{data.get('total_count')}</strong>
                    exception activities were detected during the latest monitoring cycle.
                    Please review the details below and take appropriate action.
                </div>

                <div class="summary">
                    <strong>Monitoring Summary</strong><br><br>
                    Total Exception Activities :
                    <strong>{data.get('total_count')}</strong><br>

                    Report Generated :
                    <strong>{datetime.now().strftime("%d-%m-%Y %I:%M %p")}</strong>
                </div>

                <h3 style="color:#003366;">
                    Failed Activity Details
                </h3>

                <table>
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
                    Kindly investigate the failed executions and perform the required corrective actions.
                </p>

                <p>
                    Regards,<br>
                    <strong>Automation Monitoring System</strong>
                </p>

            </div>

            <div class="footer">
                This is a system-generated email. Please do not reply to this mailbox.<br>
                
            </div>

        </div>

        </body>
        </html>
        """

        email_payload = {
            "message": {
                "subject": data.get(
                    "subject",
                    ""
                ),
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "toRecipients": build_recipients(
                    mail_to
                )
            },
            "saveToSentItems": True
        }

        cc_recipients = build_recipients(
            data.get("mail_cc")
        )

        if cc_recipients:
            email_payload["message"][
                "ccRecipients"
            ] = cc_recipients

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


