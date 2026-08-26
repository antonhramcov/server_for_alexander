import requests

from config import BOT_MODERATOR_IDS, BOT_TOKEN, TELEGRAM_PROXY_URL, TELEGRAM_REQUEST_TIMEOUT


def redact_bot_token(value: object) -> str:
    return str(value).replace(BOT_TOKEN, '<hidden_bot_token>')


def get_telegram_proxies() -> dict[str, str] | None:
    if not TELEGRAM_PROXY_URL:
        return None

    return {
        "http": TELEGRAM_PROXY_URL,
        "https": TELEGRAM_PROXY_URL,
    }


def send_request_notification(text: str, request_id: str, selected_companies: list[str]) -> bool:
    if not BOT_TOKEN:
        return False

    keyboard = []
    for index, company in enumerate(selected_companies, start=1):
        keyboard.append(
            [{"text": f"✅{company}✅", "callback_data": f"{index}-yes"}]
        )

    keyboard.append(
        [
            {"text": "Отправить", "callback_data": f"send_{request_id}"},
            {"text": "Удалить", "callback_data": f"del_{request_id}"},
        ]
    )

    sent = False
    for moderator_id in BOT_MODERATOR_IDS:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": moderator_id,
                    "text": text,
                    "reply_markup": {"inline_keyboard": keyboard},
                },
                proxies=get_telegram_proxies(),
                timeout=TELEGRAM_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            sent = True
        except requests.RequestException as exc:
            print(f"[TELEGRAM] Notification failed for {moderator_id}: {redact_bot_token(repr(exc))}")
            continue
    return sent
