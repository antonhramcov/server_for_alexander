import requests

from config import BOT_MODERATOR_ID, BOT_TOKEN


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

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": BOT_MODERATOR_ID,
                "text": text,
                "reply_markup": {"inline_keyboard": keyboard},
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return False
    return True
