import os
import re
import json
import requests

EVENT_URL = "https://www.opentix.life/event/2030899364712869889"
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def check_ticket_availability():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(EVENT_URL, headers=headers, timeout=15)
    response.raise_for_status()

    matches = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        response.text,
        re.DOTALL,
    )
    for raw in matches:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        offers = data.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        availability = offers.get("availability", "")
        if availability:
            return availability, data.get("name", "活動")

    return None, "活動"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=10,
    )


def main():
    availability, event_name = check_ticket_availability()

    print(f"活動：{event_name}")
    print(f"票務狀態：{availability}")

    if availability and "SoldOut" not in availability:
        message = (
            "🎫 <b>票源釋出！</b>\n\n"
            f"活動：{event_name}\n"
            f"狀態：{availability}\n\n"
            f"<a href=\"{EVENT_URL}\">立即購票</a>"
        )
        send_telegram(message)
        print("已發送 Telegram 通知！")
    else:
        print("目前仍為完售，持續監控中...")


if __name__ == "__main__":
    main()
