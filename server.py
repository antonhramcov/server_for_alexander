import random
import string

from flask import Flask, request
from flask_cors import CORS

from config import FLASK_HOST, FLASK_PORT
from models import from_json_to_text, save_request
from parser import get_list_companies
from telegram_notifier import send_request_notification


app = Flask(__name__)
cors = CORS(
    app,
    resource={
        r"/*": {
            "origins": "*",
            "supports_credentials": True,
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"],
        }
    },
)


@app.route('/get_names_companies_from_standarts', methods=['POST', 'OPTIONS'])
def get_names():
    if request.method == 'OPTIONS':
        return '', 200

    body = request.get_json(force=True)
    standarts = body['standarts']
    region = body['region']
    options, urls = get_list_companies(standarts, region)
    return {"status": "ok", "options": options, "urls": urls}


@app.route('/send_request', methods=['POST', 'OPTIONS'])
def send_request():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return {'status': 'ok'}

    json_data = request.json
    unical_id = ''.join([random.choice(string.hexdigits) for _ in range(32)])
    save_request(json_data, unical_id)
    send_request_notification(
        from_json_to_text(json_data),
        unical_id,
        json_data.get("selectedCompanies", []),
    )
    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
