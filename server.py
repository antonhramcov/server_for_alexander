import random, string, json, os
from flask import Flask, request, jsonify, json
from models import *
from parser_old import *
from flask_cors import CORS
import bot, requests

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

# Дает список стандартов
@app.route('/get_names_companies_from_standarts', methods=['POST', 'OPTIONS'])
def get_names():
    if request.method == 'OPTIONS':
        return '', 200
    elif request.method == 'POST':
        body = request.get_json(force=True)
        standarts = body['standarts']
        region = body['region']
        return {"status": "ok", "options": get_list_companies(standarts, region)[0]}

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
