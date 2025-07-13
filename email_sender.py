import smtplib, models
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

email = 
password = 

def send_email(address, path_to_json):
    # Тема письма
    msg = models.make_email_from_json(path_to_json)
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP('smtp.yandex.ru', 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'

def send_bad_email(address):
    msg = MIMEMultipart()
    with open('bad_answer.txt', 'r') as f:
        sample = f.read()
    msg['Subject'] = 'Audit Advisor: Ваш запрос на сертификацию отклонён'
    msg.attach(MIMEText(sample, 'plain'))
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP('smtp.yandex.ru', 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'

def send_answer(address):
    msg = MIMEMultipart()
    with open('answer.txt', 'r') as f:
        sample = f.read()
    msg['Subject'] = '​Audit Advisor: Подтверждение успешной отправки запроса на сертификациюн'
    msg.attach(MIMEText(sample, 'plain'))
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP('smtp.yandex.ru', 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'
