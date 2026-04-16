import os
import re
import json
import datetime
import requests

# ========== 在這裡新增或刪除要監控的活動 URL ==========
EVENT_URLS = [
    "https://www.opentix.life/event/2030899364712869889",
    #"https://www.opentix.life/event/1991412650162671616",
    # "https://www.opentix.life/event/再一個活動ID",
]
# ====================================================

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def check_ticket_availability(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
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
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    print(f"台灣時間：{now.strftime('%m/%d %H:%M')}")
    print(f"監控活動數：{len(EVENT_URLS)}")
    print("-" * 40)

    available_events = []
    all_results = []

    for event_url in EVENT_URLS:
        try:
            availability, event_name = check_ticket_availability(event_url)
            all_results.append((event_name, availability, event_url))
            print(f"活動：{event_name}")
            print(f"票務狀態：{availability}")

            if availability and "SoldOut" not in availability:
                available_events.append((event_name, availability, event_url))
        except Exception as e:
            print(f"檢查失敗：{event_url} - {e}")

        print("-" * 40)

    # 有票 → 立即通知
    if available_events:
        for name, status, url in available_events:
            message = (
                "🎫 <b>有票快搶！</b>\n\n"
                f"活動：{name}\n"
                f"狀態：{status}\n\n"
                f"<a href=\"{url}\">立即購票</a>"
            )
            send_telegram(message)
            print(f"已發送通知：{name}")

    # 每次執行都發心跳通知
    else:
        lines = [f"📡 監控中（{now.strftime('%m/%d %H:%M')}）\n"]
        for name, availability, url in all_results:
            status = "完售" if availability and "SoldOut" in availability else (availability or "未知")
            lines.append(f"• {name}：{status}")
        lines.append("\n系統正常運作中，有票會立即通知你。")
        send_telegram("\n".join(lines))
        print("已發送心跳通知")
    else:
        print("目前仍為完售，持續監控中...")


if __name__ == "__main__":
    main()
