import random, string
from flask import Flask, request
from models import *
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Поиск компаний по стандартам
@app.route('/search_companies')
def search_from_standarts():
    return search_companies(get_args_from_url(request.url)['standarts'])

# Дает список стандартов
@app.route('/get_names_companies_from_standarts', methods=['GET','POST'])
def hello_world():
    if request.method == 'POST':
        data = request.get_json()
        return {"status": "ok", "options": get_names_companies_for_request(search_companies(data['standarts']))}
    elif request.method == 'GET':
        return {"status": "ok", "options": get_names_companies_for_request(search_companies(request.form.getlist('standarts')))}

# Получение заявки
@app.route('/send_request', methods=['POST'])
def send_request():
    data = request.get_json()
    unical_id = ''.join([random.choice(string.hexdigits) for _ in range(32)])
    save_request(data, unical_id)
    bot_send_message(from_json_to_text(data), unical_id)
    return '200'


if __name__ == '__main__':
    app.run(debug=True)
