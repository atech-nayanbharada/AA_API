import json
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


def historical_main(cloud_loginData):
    print("Main function called")

    # --------------------------------
    # Configuration
    # --------------------------------

    HOURS = 1

    USERNAMES = ["woco101", "woco102", "woco103", "woco104", "woco105", "woco106", "woco107",
     "woco108", "woco109", "woco110", "woco111", "woco112", "woco113", "woco114"]

    # --------------------------------
    # Get token
    # --------------------------------

    token = get_token()
    print(token)

    if not token:
        print("Failed to get token.")
        return

    # --------------------------------
    # Get activities
    # --------------------------------

    data = get_task_list(token)

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
        usernames=USERNAMES
    )

    # Save API response to JSON file
    with open("bot_data.json", "w", encoding="utf-8") as file:
        json.dump(
            filtered_activities,
            file,
            indent=4,
            ensure_ascii=False
        )


    print(filtered_activities)
    email_data = {
        "subject": "[Action Required] AA Production Bot Failures",
        "activities": filtered_activities,
        "total_count": len(filtered_activities)
    }
    if len(filtered_activities) > 0:
        send_email_notification(email_data)

    else:
        print("")

    # print(
    #     f"Activities in last {HOURS} hour(s): "
    #     f"{len(filtered_activities)}"
    # )
    #
    # print(
    #     "Users:",
    #     ", ".join(USERNAMES)
    # )
    #
    # # --------------------------------
    # # Summary
    # # --------------------------------
    #
    # print_summary(filtered_activities)

    # data = get_bot_list(token)
    #
    # if not data:
    #     print("No bot data received")
    #     return
    #
    # # print(data)
    #
    # # Save API response to JSON file
    # with open("bot_data.json", "w", encoding="utf-8") as file:
    #     json.dump(
    #         data,
    #         file,
    #         indent=4,
    #         ensure_ascii=False
    #     )
    #
    # print("Bot data saved to bot_data.json")
