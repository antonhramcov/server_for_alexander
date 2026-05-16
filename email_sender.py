import smtplib
from pathlib import Path
from tempfile import NamedTemporaryFile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import models
from config import SMTP_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT


email = SMTP_EMAIL
password = SMTP_PASSWORD


def send_email(address, path_to_json):
    if not isinstance(path_to_json, (str, Path)):
        with NamedTemporaryFile(mode='wb', suffix='.json', delete=True) as temp_file:
            temp_file.write(path_to_json.data)
            temp_file.flush()
            msg = models.make_email_from_json(temp_file.name)
    else:
        msg = models.make_email_from_json(path_to_json)
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'


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
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'


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
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'
