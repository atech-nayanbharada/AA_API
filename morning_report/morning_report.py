import os

from get_token_from_api.get_api_through_token import get_token
from send_email.daily_morning_email import send_email_notification_morning
from send_email.send_email import send_email_notification
from .get_historic_custom_payload import get_custom_task_list

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def filter_activities(activities, usernames=None):
    """
    Filter activities:
    - From yesterday 07:00 PM IST
    - Until current time
    - Optionally filter by usernames
    """

    ist = ZoneInfo("Asia/Kolkata")

    # Current time in IST
    now = datetime.now(ist)

    # Yesterday
    yesterday = now.date() - timedelta(days=1)

    # Yesterday at 07:00 PM IST
    start_time = datetime(
        year=yesterday.year,
        month=yesterday.month,
        day=yesterday.day,
        hour=19,
        minute=0,
        second=0,
        tzinfo=ist
    )

    print(f"Filter Start Time : {start_time}")
    print(f"Filter End Time   : {now}")

    filtered = []

    for activity in activities:

        # -------------------------
        # Username filter
        # -------------------------
        if usernames:
            activity_username = str(
                activity.get("userName", "")
            ).strip()

            if activity_username not in usernames:
                continue

        # -------------------------
        # Get endDateTime
        # -------------------------
        end_date_time = activity.get("endDateTime")

        if not end_date_time:
            continue

        try:
            # AA timestamp is UTC
            end_time_utc = datetime.fromisoformat(
                end_date_time.replace("Z", "+00:00")
            )

            # Convert UTC -> IST
            end_time_ist = end_time_utc.astimezone(ist)

        except (ValueError, TypeError):
            print(
                f"Invalid endDateTime: {end_date_time}"
            )
            continue

        # -------------------------
        # Date/time filter
        # -------------------------
        if start_time <= end_time_ist <= now:
            filtered.append(activity)

    return filtered

def morning_report_main(config_list):

    all_failed_activities = []
    all_completed_activities = []

    for base_cloud_login_data in config_list:

        # --------------------------------
        # Configuration
        # --------------------------------
        runner_list = [
            runner.strip()
            for runner in str(
                base_cloud_login_data.get("Historic_Runner_List", "")
            ).split(",")
            if runner.strip()
        ]

        # --------------------------------
        # Get token
        # --------------------------------
        token = get_token(base_cloud_login_data)

        if not token:
            print("Failed to get token.")
            continue

        # ============================================================
        # FAILED ACTIVITIES
        # ============================================================

        failed_status_list = [
            "RUN_ABORTED",
            "RUN_TIMED_OUT",
            "DEPLOY_FAILED",
            "RUN_FAILED"
        ]

        failed_operands = [
            {
                "operator": "eq",
                "field": "status",
                "value": status
            }
            for status in failed_status_list
        ]

        failed_data = get_custom_task_list(
            token,
            base_cloud_login_data,
            failed_operands
        )

        if failed_data:

            failed_activities = failed_data.get("list", [])

            print(
                "Total failed activities received:",
                len(failed_activities)
            )

            filtered_failed = filter_activities(
                failed_activities,
                usernames=runner_list
            )

            all_failed_activities.extend(filtered_failed)

        # ============================================================
        # COMPLETED ACTIVITIES
        # ============================================================

        completed_operands = [
            {
                "operator": "eq",
                "field": "status",
                "value": "COMPLETED"
            }
        ]

        completed_data = get_custom_task_list(
            token,
            base_cloud_login_data,
            completed_operands
        )

        if completed_data:

            completed_activities = completed_data.get("list", [])

            print(
                "Total completed activities received:",
                len(completed_activities)
            )

            filtered_completed = filter_activities(
                completed_activities,
                usernames=runner_list
            )

            all_completed_activities.extend(filtered_completed)

    # ============================================================
    # EMAIL DATA
    # ============================================================

    email_data = {
        "subject": "AA Production Bot Execution Monitoring Report",
        "email_title": "Automation Anywhere Monitoring Report",
        "environment_name": "Production",

        # Separate lists
        "failed_activities": all_failed_activities,
        "completed_activities": all_completed_activities,

        # Separate counts
        "failed_count": len(all_failed_activities),
        "completed_count": len(all_completed_activities),

        "total_count": (
            len(all_failed_activities)
            + len(all_completed_activities)
        ),

        "mail_cc": os.getenv("CC_EMAIL", ""),
        "sender_email": os.getenv("SENDER_EMAIL"),
        "mail_to": os.getenv("RECEIVER_EMAIL")
    }

    # Send email if either failed or completed activities exist
    if all_failed_activities or all_completed_activities:

        email_sent = send_email_notification_morning(email_data)

        if email_sent:
            print("Morning report sent successfully.")
        else:
            print("Morning report could not be sent.")

    else:
        print(
            "No bot activities found for the selected time period. "
            "Email was not sent."
        )