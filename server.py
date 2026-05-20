import random
import string
from io import BytesIO

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from config import FLASK_HOST, FLASK_PORT
from models import (
    add_user,
    from_json_to_text,
    list_binary_files,
    load_binary_file,
    load_request,
    save_binary_file,
    save_cache_data,
    save_request,
    write_request,
)
from parser import add_count_current_month, get_list_companies, get_list_emails
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
    standarts = body.get('standarts') or body.get('standards') or []
    region = body.get('region') or body.get('Region') or '50'
    country = body.get('country') or body.get('Country') or 'russia'
    options, urls = get_list_companies(standarts, region, country)
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


@app.route('/internal/requests/<request_id>', methods=['GET', 'PUT', 'DELETE'])
def internal_request(request_id: str):
    if request.method == 'GET':
        return load_request(request_id)

    if request.method == 'PUT':
        payload = request.get_json(force=True)
        write_request(payload, request_id)
        return {"status": "ok"}

    request_path = f"{request_id}.json"
    from config import REQUESTS_DIR
    (REQUESTS_DIR / request_path).unlink(missing_ok=True)
    return {"status": "ok"}


@app.route('/internal/requests/<request_id>/document', methods=['GET'])
def internal_request_document(request_id: str):
    from config import REQUESTS_DIR

    request_path = REQUESTS_DIR / f"{request_id}.json"
    return send_file(
        request_path,
        mimetype='application/json',
        as_attachment=True,
        download_name='request.json',
    )


@app.route('/internal/files', methods=['GET'])
def internal_files():
    return {"files": list_binary_files()}


@app.route('/internal/files/<path:filename>', methods=['GET', 'PUT'])
def internal_file(filename: str):
    if request.method == 'GET':
        content = load_binary_file(filename)
        return send_file(
            BytesIO(content),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream',
        )

    save_binary_file(filename, request.get_data())
    return {"status": "ok"}


@app.route('/internal/users', methods=['POST'])
def internal_users():
    payload = request.get_json(force=True)
    add_user(payload["id"], payload.get("username"))
    return {"status": "ok"}


@app.route('/internal/companies/emails', methods=['POST'])
def internal_company_emails():
    payload = request.get_json(force=True)
    return {"emails": get_list_emails(payload["companies"], payload.get("country", "russia"))}


@app.route('/internal/companies/increment', methods=['POST'])
def internal_company_increment():
    payload = request.get_json(force=True)
    for company in payload["companies"]:
        add_count_current_month(company, payload.get("country", "russia"))
    return {"status": "ok"}


@app.route('/internal/cache/sync', methods=['POST'])
def internal_cache_sync():
    payload = request.get_json(force=True)
    save_cache_data(payload["data1"], payload["data3"])
    return {"status": "ok"}


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
