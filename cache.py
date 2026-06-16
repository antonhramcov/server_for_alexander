import json

from gspread.exceptions import GSpreadException

from config import (
    CACHE_RUSSIA_COMPANIES_SHEET,
    CACHE_RUSSIA_LIMITS_SHEET,
    CACHE_SPREADSHEET_URL,
    CACHE_USA_SHEET,
    DATA_US_PATH,
)
from google_client import get_gspread_client
from models import save_cache_data


RUSSIA_COMPANY_HEADERS = {"Номер записи в РАЛ (1)", "Сокращенное наименование", "Код региона"}
RUSSIA_LIMIT_HEADERS = {"Certification_body", "Registration_number", "cb_region_number"}
USA_COMPANY_HEADERS = {"Company_name", "Region_short", "Accreditation_link"}


def compact_rows(rows: list[dict], primary_key: str | None = None) -> list[dict]:
    compacted: list[dict] = []
    for row in rows:
        if not any(str(value).strip() for value in row.values()):
            continue
        if primary_key and not str(row.get(primary_key, "")).strip():
            continue
        compacted.append(row)
    return compacted


def load_existing_us_cache() -> list[dict]:
    if not DATA_US_PATH.exists():
        return []
    with open(DATA_US_PATH) as f:
        return json.load(f)


def classify_sheet(title: str, rows: list[dict]) -> str | None:
    headers = set(rows[0].keys()) if rows else set()
    title_normalized = title.strip().lower()

    if RUSSIA_COMPANY_HEADERS.issubset(headers):
        return "russia_companies"
    if RUSSIA_LIMIT_HEADERS.issubset(headers):
        return "russia_limits"
    if USA_COMPANY_HEADERS.issubset(headers):
        return "usa_companies"
    if "usa" in title_normalized and "company_name" in {header.lower() for header in headers}:
        return "usa_companies"
    return None


def get_rows(worksheet, primary_key: str | None = None) -> list[dict]:
    return compact_rows(worksheet.get_all_records(), primary_key=primary_key)


def get_detectable_rows(worksheet) -> list[dict]:
    try:
        return compact_rows(worksheet.get_all_records())
    except GSpreadException as exc:
        print(f"Skipping worksheet '{worksheet.title}': {exc}")
        return []


def log_usa_diagnostics(rows: list[dict]) -> None:
    companies = [
        {
            "Company_name": str(row.get("Company_name", "")).strip(),
            "Email": str(row.get("Email", "")).strip(),
        }
        for row in rows
    ]
    companies = [row for row in companies if row["Company_name"]]
    with_email = sum(1 for row in companies if row["Email"])
    preview = companies[:5]
    print(
        f"USA diagnostics: rows={len(companies)}, rows_with_email={with_email}, "
        f"preview={preview}"
    )


def find_sheets(sh) -> dict[str, list[dict]]:
    sheets: dict[str, list[dict]] = {}
    manual_titles = {
        "russia_companies": (CACHE_RUSSIA_COMPANIES_SHEET, "Номер записи в РАЛ (1)"),
        "russia_limits": (CACHE_RUSSIA_LIMITS_SHEET, "Certification_body"),
        "usa_companies": (CACHE_USA_SHEET, "Company_name"),
    }

    for sheet_key, (sheet_title, primary_key) in manual_titles.items():
        if not sheet_title:
            continue
        rows = get_rows(sh.worksheet(sheet_title), primary_key=primary_key)
        sheets[sheet_key] = rows
        print(f"Loaded {sheet_key} from worksheet '{sheet_title}' with {len(rows)} rows")
        if sheet_key == "usa_companies":
            log_usa_diagnostics(rows)

    for worksheet in sh.worksheets():
        rows = get_detectable_rows(worksheet)
        sheet_key = classify_sheet(worksheet.title, rows)
        if not sheet_key or sheet_key in sheets:
            continue

        primary_key = {
            "russia_companies": "Номер записи в РАЛ (1)",
            "russia_limits": "Certification_body",
            "usa_companies": "Company_name",
        }[sheet_key]
        rows = compact_rows(rows, primary_key=primary_key)
        sheets[sheet_key] = rows
        print(f"Detected {sheet_key} from worksheet '{worksheet.title}' with {len(rows)} rows")
        if sheet_key == "usa_companies":
            log_usa_diagnostics(rows)

    return sheets


def refresh_cache():
    gc = get_gspread_client()
    sh = gc.open_by_url(CACHE_SPREADSHEET_URL)
    sheets = find_sheets(sh)

    missing_required = [key for key in ("russia_companies", "russia_limits") if key not in sheets]
    if missing_required:
        raise RuntimeError(f"Required worksheets were not detected: {', '.join(missing_required)}")

    data_us = sheets.get("usa_companies")
    if data_us is None:
        data_us = load_existing_us_cache()
        print(f"USA worksheet not detected, keeping existing data_us.json with {len(data_us)} rows")

    save_cache_data(sheets["russia_companies"], sheets["russia_limits"], data_us)
    print("Cache updated successfully")


if __name__ == '__main__':
    refresh_cache()
