from io import BytesIO
from pathlib import Path

import requests

from config import INTERNAL_API_TIMEOUT, INTERNAL_API_URL


def _url(path: str) -> str:
    return f"{INTERNAL_API_URL.rstrip('/')}{path}"


def get_request(request_id: str) -> dict:
    response = requests.get(_url(f"/internal/requests/{request_id}"), timeout=INTERNAL_API_TIMEOUT)
    response.raise_for_status()
    return response.json()


def update_request(request_id: str, payload: dict) -> dict:
    response = requests.put(
        _url(f"/internal/requests/{request_id}"),
        json=payload,
        timeout=INTERNAL_API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def delete_request(request_id: str) -> None:
    response = requests.delete(_url(f"/internal/requests/{request_id}"), timeout=INTERNAL_API_TIMEOUT)
    response.raise_for_status()


def get_request_document(request_id: str) -> bytes:
    response = requests.get(
        _url(f"/internal/requests/{request_id}/document"),
        timeout=INTERNAL_API_TIMEOUT,
    )
    response.raise_for_status()
    return response.content


def list_files() -> list[str]:
    response = requests.get(_url("/internal/files"), timeout=INTERNAL_API_TIMEOUT)
    response.raise_for_status()
    return response.json()["files"]


def download_file(filename: str) -> bytes:
    response = requests.get(_url(f"/internal/files/{filename}"), timeout=INTERNAL_API_TIMEOUT)
    response.raise_for_status()
    return response.content


def upload_file(filename: str, content: bytes) -> None:
    response = requests.put(
        _url(f"/internal/files/{filename}"),
        data=content,
        timeout=INTERNAL_API_TIMEOUT,
        headers={"Content-Type": "application/octet-stream"},
    )
    response.raise_for_status()


def create_user(user_id: int, username: str | None) -> None:
    response = requests.post(
        _url("/internal/users"),
        json={"id": user_id, "username": username or ""},
        timeout=INTERNAL_API_TIMEOUT,
    )
    response.raise_for_status()


def get_company_emails(companies: list[str], country: str = "russia") -> list[str]:
    response = requests.post(
        _url("/internal/companies/emails"),
        json={"companies": companies, "country": country},
        timeout=INTERNAL_API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["emails"]


def increment_company_counts(companies: list[str], country: str = "russia") -> None:
    response = requests.post(
        _url("/internal/companies/increment"),
        json={"companies": companies, "country": country},
        timeout=INTERNAL_API_TIMEOUT,
    )
    response.raise_for_status()


def sync_cache(data1: list[dict], data3: list[dict]) -> None:
    response = requests.post(
        _url("/internal/cache/sync"),
        json={"data1": data1, "data3": data3},
        timeout=INTERNAL_API_TIMEOUT,
    )
    response.raise_for_status()
