import os
from datetime import datetime, timedelta, timezone
from send_email.send_email import send_email_notification
from get_token_from_api.get_api_through_token import get_token
from historical_data_operation.get_historic_data import get_task_list


def filter_activities(activities, hours=1, usernames=None):
    """
    Filter activities by:
    - Last N hours
    - Optional list of usernames

    usernames=None -> all users
    usernames=["woco108"] -> only woco108
    usernames=["woco108", "john"] -> woco108 OR john
    """

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    filtered = []

    for activity in activities:
        # -------------------------
        # Username filter
        # -------------------------
        if usernames:
            activity_username = activity.get("userName")
            if activity_username not in usernames:
                continue

        # -------------------------
        # Date filter
        # -------------------------
        end_date_time = activity.get("endDateTime")

        if not end_date_time:
            continue

        try:
            end_time = datetime.fromisoformat(
                end_date_time.replace("Z", "+00:00")
            )
        except ValueError:
            print(f"Invalid endDateTime: {end_date_time}")
            continue

        if start_time <= end_time <= now:
            filtered.append(activity)
    return filtered


def print_summary(activities):

    status_count = {}

    for activity in activities:
        status = activity.get("status", "UNKNOWN")

        status_count[status] = (
            status_count.get(status, 0) + 1
        )

    print("\n" + "=" * 40)
    print("ACTIVITY SUMMARY")
    print("=" * 40)

    for status, count in status_count.items():
        print(f"{status:<20}: {count}")

    print("-" * 40)
    print(f"{'TOTAL':<20}: {len(activities)}")
    print("=" * 40)


def historical_main(config_list):
    all_filtered_activities_list = []
    for base_cloud_login_data in config_list:
        # --------------------------------
        # Configuration
        # --------------------------------
        runner_list = [runner.strip() for runner in str(base_cloud_login_data.get("Historic_Runner_List", "")).split(",") if runner.strip()]
        HOURS = 1
        # --------------------------------
        # Get token
        # --------------------------------

        token = get_token(base_cloud_login_data)
        if not token:
            print("Failed to get token.")
            return

        # --------------------------------
        # Get activities
        # --------------------------------

        data = get_task_list(token, base_cloud_login_data)
        if not data:
            print("No data received.")
            return

        activities = data.get("list", [])

        print(
            "Total activities received:",
            len(activities)
        )

        # --------------------------------
        # Filter
        # --------------------------------
        filtered_activities = filter_activities(
            activities,
            hours=HOURS,
            usernames=runner_list
        )
        all_filtered_activities_list = all_filtered_activities_list + filtered_activities


    email_data = {
        "subject": (
            f"[Action Required] AA Production Bot Failures"
        ),
        "email_title": "Automation Anywhere Monitoring Alert",
        "environment_name": "Production",
        "activities": all_filtered_activities_list,
        "total_count": len(all_filtered_activities_list),
        "mail_cc": os.getenv("CC_EMAIL", ""),
        "sender_email": os.getenv("SENDER_EMAIL"),
        "mail_to": os.getenv("RECEIVER_EMAIL")
    }

    if all_filtered_activities_list:
        email_sent = send_email_notification(email_data)
        if email_sent:
            print("Failure notification sent successfully.")
        else:
            print("Failure notification could not be sent.")

    else:
        print("No failed bot activities found. Email was not sent.")



