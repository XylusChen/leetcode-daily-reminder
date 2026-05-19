import requests
import os
import json
from datetime import datetime, timezone

def fetch_daily_problem():
    response = requests.get("https://alfa-leetcode-api.onrender.com/daily/raw", timeout=15)
    response.raise_for_status()
    return response.json()

def fetch_user_profile(username):
    response = requests.get(f"https://alfa-leetcode-api.onrender.com/{username}/profile", timeout=15)
    response.raise_for_status()
    return response.json()

def is_solved_today(title_slug, recent_submissions):
    """Check if the daily problem was solved (Accepted) today in UTC."""
    now_utc = datetime.now(timezone.utc)
    # LeetCode resets at midnight UTC, so today starts at 00:00:00 UTC
    today_midnight_utc = int(datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc).timestamp())

    for submission in recent_submissions:
        if (
            submission["titleSlug"] == title_slug
            and submission["statusDisplay"] == "Accepted"
            and int(submission["timestamp"]) >= today_midnight_utc
        ):
            return True
    return False

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("Message sent successfully!")

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    username = "XylusChen"

    daily_data = fetch_daily_problem()
    daily = daily_data["activeDailyCodingChallengeQuestion"]
    question = daily["question"]

    title = question["title"]
    title_slug = question["titleSlug"]
    difficulty = question["difficulty"]
    link = f"https://leetcode.com{daily['link']}"

    stats = json.loads(question["stats"])
    total_accepted = stats["totalAccepted"]
    total_submissions = stats["totalSubmission"]
    acceptance_rate = stats["acRate"]

    difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(difficulty, "⚪")
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    profile_data = fetch_user_profile(username)
    recent_submissions = profile_data["recentSubmissions"]
    solved_today = is_solved_today(title_slug, recent_submissions)

    if solved_today:
        message = (
            f"🎉 *Daily Challenge Complete!*\n\n"
            f"You've already crushed today's problem — well done!\n\n"
            f"*{title}* {difficulty_emoji}\n"
            f"🔗 [View problem]({link})\n\n"
            f"🔥 Keep that streak alive. See you tomorrow!"
        )
    else:
        message = (
            f"🧩 *LeetCode Daily — {today}*\n\n"
            f"*{title}*\n"
            f"{difficulty_emoji} Difficulty: `{difficulty}`\n\n"
            f"📊 *Stats*\n"
            f"✅ Accepted: `{total_accepted}`\n"
            f"📬 Total Submissions: `{total_submissions}`\n"
            f"📈 Acceptance Rate: `{acceptance_rate}`\n\n"
            f"🔗 [Solve it here]({link})"
        )

    send_telegram_message(token, chat_id, message)

if __name__ == "__main__":
    main()