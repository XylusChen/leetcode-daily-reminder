import requests
import os
import time
import random
from datetime import datetime, timezone

LEETCODE_GQL = "https://leetcode.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0"
}

DAILY_QUERY = """
query {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      title
      titleSlug
      difficulty
      stats
    }
  }
}
"""

PROFILE_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    title
    titleSlug
    timestamp
  }
}
"""

def gql_request(query, variables=None, max_retries=5, base_delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                LEETCODE_GQL,
                json={"query": query, "variables": variables or {}},
                headers=HEADERS,
                timeout=15
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == max_retries:
                    resp.raise_for_status()
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 2)
                print(f"Attempt {attempt} got {resp.status_code}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp.json()["data"]
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 2)
            print(f"Attempt {attempt} failed ({e}). Retrying in {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError("Failed after max retries")

def fetch_daily_problem():
    data = gql_request(DAILY_QUERY)
    return data["activeDailyCodingChallengeQuestion"]

def fetch_recent_ac_submissions(username, limit=20):
    data = gql_request(PROFILE_QUERY, {"username": username, "limit": limit})
    return data["recentAcSubmissionList"]

def is_solved_today(title_slug, recent_submissions):
    now_utc = datetime.now(timezone.utc)
    today_midnight_utc = int(datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc).timestamp())
    for submission in recent_submissions:
        if submission["titleSlug"] == title_slug and int(submission["timestamp"]) >= today_midnight_utc:
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

    daily = fetch_daily_problem()
    question = daily["question"]

    title = question["title"]
    title_slug = question["titleSlug"]
    difficulty = question["difficulty"]
    link = f"https://leetcode.com{daily['link']}"

    stats = eval(question["stats"]) if isinstance(question["stats"], str) and question["stats"].startswith("{") else {}
    # LeetCode's GraphQL 'stats' field is a JSON string just like alfa's — parse safely:
    import json as _json
    stats = _json.loads(question["stats"])
    total_accepted = stats["totalAccepted"]
    total_submissions = stats["totalSubmission"]
    acceptance_rate = stats["acRate"]

    difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(difficulty, "⚪")
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    recent_submissions = fetch_recent_ac_submissions(username)
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
