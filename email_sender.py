from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests

import models
from config import EMAIL_API_TIMEOUT, EMAIL_SENDER_NAME, RESEND_API_KEY, RESEND_API_URL, SMTP_EMAIL


NETWORK_CHECK_URL = urlparse(RESEND_API_URL)
NETWORK_CHECK_SCHEME = NETWORK_CHECK_URL.scheme or "https"
NETWORK_CHECK_HOST = NETWORK_CHECK_URL.hostname or "api.resend.com"
NETWORK_CHECK_PORT = NETWORK_CHECK_URL.port or (443 if NETWORK_CHECK_URL.scheme == "https" else 80)
sender_email = SMTP_EMAIL


def _sender_value() -> str:
    return sender_email if not EMAIL_SENDER_NAME else f"{EMAIL_SENDER_NAME} <{sender_email}>"


def _extract_text_body(msg: MIMEMultipart) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() != 'text/plain':
                continue
            payload = part.get_payload(decode=True)
            charset = part.get_content_charset() or 'utf-8'
            if payload is None:
                return str(part.get_payload())
            return payload.decode(charset, errors='replace')
        return ""

    payload = msg.get_payload(decode=True)
    charset = msg.get_content_charset() or 'utf-8'
    if payload is None:
        return str(msg.get_payload())
    return payload.decode(charset, errors='replace')


def _build_html_body(text_content: str) -> str:
    return f'<pre style="font-family:inherit;white-space:pre-wrap">{escape(text_content)}</pre>'


def _deliver_message(address: str, msg: MIMEMultipart) -> str:
    if not RESEND_API_KEY:
        return 'Обнаружена ошибка: не задан RESEND_API_KEY'
    if not sender_email:
        return 'Обнаружена ошибка: не задан SMTP_EMAIL для отправителя'

    text_content = _extract_text_body(msg)
    payload = {
        "from": _sender_value(),
        "to": [address],
        "subject": msg.get('Subject', ''),
        "html": _build_html_body(text_content),
        "text": text_content,
    }

    try:
        response = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=EMAIL_API_TIMEOUT,
        )
        data = response.json()
        response.raise_for_status()
    except Exception as e:
        return f'Обнаружена ошибка {e}'

    if data.get("error"):
        message = data["error"].get("message") if isinstance(data.get("error"), dict) else data.get("error")
        return f'Обнаружена ошибка Resend: {message or "Неизвестная ошибка"}'

    return f'Письмо было отправлено на {address}'

def send_email(address, path_to_json):
    if not isinstance(path_to_json, (str, Path)):
        with NamedTemporaryFile(mode='wb', suffix='.json', delete=True) as temp_file:
            temp_file.write(path_to_json.data)
            temp_file.flush()
            msg = models.make_email_from_json(temp_file.name)
    else:
        msg = models.make_email_from_json(path_to_json)
    return _deliver_message(address, msg)


def send_bad_email(address, country="russia"):
    msg = MIMEMultipart()
    sample = models.load_template('bad', country)
    fallback_subjects = {
        "russia": 'Audit Advisor: Ваш запрос на сертификацию отклонён',
        "usa": 'Audit Advisor: Your Certification Request Was Not Approved',
        "uk": 'Audit Advisor: Your Certification Request Was Not Approved',
    }
    normalized_country = models.normalize_country(country)
    subject, body = models.split_subject_and_body(sample, fallback_subjects[normalized_country])
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return _deliver_message(address, msg)


def send_answer(address, country="russia"):
    msg = MIMEMultipart()
    sample = models.load_template('success', country)
    fallback_subjects = {
        "russia": 'Audit Advisor: Подтверждение успешной отправки запроса на сертификацию',
        "usa": 'Audit Advisor: Your Certification Request Has Been Successfully Submitted',
        "uk": 'Audit Advisor: Your Certification Request Has Been Successfully Submitted',
    }
    normalized_country = models.normalize_country(country)
    subject, body = models.split_subject_and_body(sample, fallback_subjects[normalized_country])
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return _deliver_message(address, msg)
