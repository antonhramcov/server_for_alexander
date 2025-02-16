import smtplib, models
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

email = 'auditadvisor@yandex.ru'
password = ''

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
