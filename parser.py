import datetime
import json
import re
from random import choice, shuffle

from config import DATA1_PATH, DATA3_PATH, DATA_UK_PATH, DATA_US_PATH


def load_json(path):
    with open(path) as f:
        return json.load(f)


def normalize_country(country: str | None) -> str:
    normalized = (country or "russia").strip().lower()
    if normalized in {"usa", "us", "united states", "america"}:
        return "usa"
    if normalized in {"uk", "united kingdom", "great britain", "britain"}:
        return "uk"
    return "russia"


def load_company_dataset(country: str) -> list[dict]:
    if country == "usa":
        data_us = load_json(DATA_US_PATH)
        return [company for company in data_us if company.get("Company_name") and company.get("Status")]
    if country == "uk":
        data_uk = load_json(DATA_UK_PATH)
        return [company for company in data_uk if company.get("Company_name") and company.get("Status")]
    return load_json(DATA1_PATH)


def normalize_standard_keys(standarts: list[str], companies: list[dict]) -> list[str]:
    if isinstance(standarts, str):
        standarts = [standarts]
    elif not isinstance(standarts, (list, tuple, set)):
        standarts = [str(standarts)]

    available_standarts = {
        key
        for company in companies
        for key, value in company.items()
        if key.isdigit() and value in {"+", "-"}
    }

    normalized_standarts = []
    for standart in standarts:
        raw_standart = str(standart).strip()
        if raw_standart in available_standarts:
            normalized_standarts.append(raw_standart)
            continue

        matched_standart = next(
            (
                code
                for code in re.findall(r"\d{4,5}", raw_standart)
                if code in available_standarts
            ),
            None,
        )
        normalized_standarts.append(matched_standart or raw_standart)

    return list(dict.fromkeys(normalized_standarts))


def get_company_display_name(company: dict, country: str) -> str:
    if country in {"usa", "uk"}:
        return f"{company['Company_name']}, {company['City_and_Region']}"
    return f"{company['Сокращенное наименование']}, {company['Город']}"


def get_company_name(company: dict, country: str) -> str:
    if country in {"usa", "uk"}:
        return company["Company_name"]
    return company["Сокращенное наименование"]


def get_company_status(company: dict, country: str) -> str:
    if country in {"usa", "uk"}:
        return company.get("Status", "")
    return company.get("Статус", "")


def get_company_region_number(company: dict, country: str) -> int | None:
    field = "Region_number" if country in {"usa", "uk"} else "Код региона"
    value = company.get(field)
    if value in ("", None):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_company_url_value(company: dict, country: str) -> str | None:
    if country in {"usa", "uk"}:
        return company.get("Website") or company.get("Accreditation_link") or None
    return company.get("Ссылка на сайт")


def get_company_email_value(company: dict, country: str) -> str:
    if country in {"usa", "uk"}:
        return (company.get("Email") or "").strip()
    return (company.get("Адрес эл. почты") or "").strip()


def find_company_by_selection(companies: list[dict], selection: str, country: str) -> dict | None:
    for company in companies:
        if get_company_display_name(company, country) == selection:
            return company

    if country == "russia":
        clean_name = selection.split(", ")[0]
        return next((company for company in companies if get_company_name(company, country) == clean_name), None)

    return next((company for company in companies if get_company_name(company, country) == selection), None)


def add_count_current_month(companie: str, country: str = "russia"):
    if normalize_country(country) != "russia":
        return

    data3 = load_json(DATA3_PATH)
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    for comp in data3:
        if comp["Certification_body"] == companie:
            comp[now] = int(comp.get(now, 0)) + 1
            with open(DATA3_PATH, 'w') as f:
                json.dump(data3, f)
            break


def order_companies(companies: list[dict], selected_region_company: list[dict], country: str) -> list[dict]:
    if country in {"usa", "uk"}:
        initial, passive, other = [], [], []
        for company in companies:
            if company in selected_region_company:
                continue
            status = get_company_status(company, country)
            if status == "Initial":
                initial.append(company)
            elif status == "Passive":
                passive.append(company)
            else:
                other.append(company)

        for current_list in (initial, passive, other):
            shuffle(current_list)

        return initial + selected_region_company + passive + other

    advanced, standard, initial, passive = [], [], [], []
    for company in companies:
        if company in selected_region_company:
            continue
        status = get_company_status(company, country)
        if status == "Продвинутый":
            advanced.append(company)
        elif status == "Стандарт":
            standard.append(company)
        elif status == "Начальный":
            initial.append(company)
        elif status == "Пассивный":
            passive.append(company)

    for current_list in (advanced, standard, initial, passive):
        shuffle(current_list)

    return advanced + selected_region_company + standard + initial + passive


def get_list_companies(standarts: list[str], region: str = "50", country: str = "russia"):
    normalized_country = normalize_country(country)
    companies = load_company_dataset(normalized_country)
    standarts = normalize_standard_keys(standarts, companies)

    filtered_companies = []
    for company in companies:
        status = get_company_status(company, normalized_country)
        if normalized_country == "russia" and status.lower() == "бан":
            continue
        if all(company.get(standart) == "+" for standart in standarts):
            filtered_companies.append(company)

    region_number = None
    try:
        region_number = int(region)
    except (TypeError, ValueError):
        pass

    regional_companies = []
    if region_number is not None:
        regional_companies = [
            company
            for company in filtered_companies
            if get_company_region_number(company, normalized_country) == region_number
        ]
    if regional_companies:
        regional_companies = [choice(regional_companies)]

    output_companies = order_companies(filtered_companies, regional_companies, normalized_country)
    output_names = [get_company_display_name(company, normalized_country) for company in output_companies]
    urls = [get_company_url_value(company, normalized_country) for company in output_companies]
    return [output_names, urls]


def get_list_emails(list_companies: list[str], country: str = "russia"):
    normalized_country = normalize_country(country)
    companies = load_company_dataset(normalized_country)
    emails = []

    for selection in list_companies:
        company = find_company_by_selection(companies, selection, normalized_country)
        if not company:
            continue

        raw_email = get_company_email_value(company, normalized_country)
        if not raw_email or raw_email.lower() == "no":
            continue

        if ", " in raw_email:
            emails.extend([email for email in raw_email.split(", ") if email])
        else:
            emails.append(raw_email)

    return emails


def get_url(companie: str, country: str = "russia"):
    normalized_country = normalize_country(country)
    companies = load_company_dataset(normalized_country)
    company = find_company_by_selection(companies, companie, normalized_country)
    if not company:
        return None
    return get_company_url_value(company, normalized_country)


def get_urls(list_companies: list[str], country: str = "russia"):
    return [get_url(company, country) for company in list_companies]
