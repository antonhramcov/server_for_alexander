import random, string, json
from flask import Flask, request, jsonify, json
from models import *
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(
    app, 
    resource={
        r"/*": {
            "origins": "*",
            "supports_credentials": True,
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"]
        }
    }
)

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Дает список стандартов
@app.route('/get_names_companies_from_standarts', methods=['GET','POST'])
def hello_world():
    if request.method == 'POST':
        standarts = find_standarts_from_str(request.get_data(as_text=True))
        return {"status": "ok", "options": get_names_companies_for_request(search_companies(standarts))}
    elif request.method == 'GET':
        return {"status": "ok", "options": get_names_companies_for_request(search_companies(request.form.getlist('standarts')))}

# Получение заявки
@app.route('/send_request', methods=['POST', 'OPTIONS'])
def send_request():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        unical_id = ''.join([random.choice(string.hexdigits) for _ in range(32)])
        save_request(json, unical_id)
        bot_send_message(from_json_to_text(json), unical_id)
        return {'status': 'ok'}
    else:
        return  {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0')
