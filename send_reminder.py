import requests
import os
import json
from datetime import datetime

def fetch_daily_problem():
    response = requests.get("https://alfa-leetcode-api.onrender.com/daily/raw", timeout=15)
    response.raise_for_status()
    return response.json()

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

    data = fetch_daily_problem()

    daily = data["activeDailyCodingChallengeQuestion"]
    question = daily["question"]

    title = question["title"]
    difficulty = question["difficulty"]
    link = f"https://leetcode.com{daily['link']}"

    stats = json.loads(question["stats"])
    total_accepted = stats["totalAccepted"]
    total_submissions = stats["totalSubmission"]
    acceptance_rate = stats["acRate"]

    difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(difficulty, "⚪")
    today = datetime.utcnow().strftime("%B %d, %Y")

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