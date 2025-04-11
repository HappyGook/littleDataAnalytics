import json
from datetime import datetime, timedelta
import random
import numpy as np
from collections import defaultdict, Counter


# Mock-data generator
def generate_uploads():
    uploads = []
    start_date = datetime.now() - timedelta(days=30)

    for day in range(30):
        date = start_date + timedelta(days=day)
        uploads_count = random.randint(1, 20)

        for _ in range(uploads_count):
            time = timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            timestamp = date + time
            uploads.append({"user_id": 1, "timestamp": timestamp.isoformat()})

    return json.dumps(uploads, indent=4)

#Getting a week from a file
def get_iso_week(dt):
    return dt.isocalendar()[1]


def analyze_uploads(data):
    timestamps = [datetime.fromisoformat(u["timestamp"]) for u in data if u["user_id"] == 1]
    timestamps.sort()

    daily_count = Counter()
    weekly_count = Counter()
    hour_count = Counter()
    weekday_count = Counter()
    iso_week_count = Counter()
    streaks = []

    last_day = None
    current_streak = 0

    for ts in timestamps:
        day_key = ts.date()
        daily_count[day_key] += 1
        weekly_count[get_iso_week(ts)] += 1
        hour_count[ts.hour] += 1
        weekday_count[ts.strftime("%A")] += 1
        iso_week_count[ts.isocalendar()[1]] += 1

        # streak tracking (days with uploads in a row)
        if last_day is None or (ts.date() - last_day == timedelta(days=1)):
            current_streak += 1
        elif ts.date() != last_day:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 1
        last_day = ts.date()

    if current_streak > 0:
        streaks.append(current_streak)

    # upload interval (avg time between uploads)
    intervals = [
        (timestamps[i] - timestamps[i - 1]).total_seconds()
        for i in range(1, len(timestamps))
    ]
    avg_interval_minutes = sum(intervals) / len(intervals) / 60 if intervals else 0
    avg_interval_hours = avg_interval_minutes / 60

    # Rolling 3-hour peak
    hours = list(range(24))
    hour_array = np.array([hour_count.get(h, 0) for h in hours])
    rolling_hour_sum = np.convolve(hour_array, np.ones(3), 'valid')
    peak_hour_start = int(np.argmax(rolling_hour_sum))
    peak_hour_range = f"{peak_hour_start}:00 to {peak_hour_start + 2}:00"

    # 3-day weekday window
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_array = np.array([weekday_count.get(day, 0) for day in weekdays])
    rolling_weekday_sum = np.convolve(weekday_array, np.ones(3), 'valid')
    peak_day_start = int(np.argmax(rolling_weekday_sum))
    peak_day_range = f"{weekdays[peak_day_start]} to {weekdays[min(peak_day_start + 2, 6)]}"

    # Longest streaks and inactivity
    longest_streak = max(streaks) if streaks else 0
    inactivity_days = 30 - len(set(daily_count.keys()))

    return {
        "average_upload_interval_minutes": round(avg_interval_minutes, 2),
        "average_upload_interval_hours": round(avg_interval_hours, 2),
        "total_uploads": len(timestamps),
        "unique_days_active": len(set(daily_count.keys())),
        "most_active_day": str(max(daily_count.items(), key=lambda x: x[1])[0]),
        "most_active_day_uploads": max(daily_count.values()),
        "busiest_week": max(weekly_count.items(), key=lambda x: x[1])[0],
        "uploads_by_hour": sorted(hour_count.items(), key=lambda x: x[1], reverse=True),
        "uploads_by_weekday": sorted(weekday_count.items(), key=lambda x: x[1], reverse=True),
        "peak_3_hour_window": peak_hour_range,
        "peak_3_day_window": peak_day_range,
        "longest_upload_streak_days": longest_streak,
        "inactive_days_count": inactivity_days,
    }


if __name__ == '__main__':
    mock_data = json.loads(generate_uploads())
    analysis = analyze_uploads(mock_data)
    print(json.dumps(analysis, indent=4))
