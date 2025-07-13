import os
from search_and_rank_companies_func import (
    build_companies,
    filter_by_standards,
    load_report_and_sync,
    rank_companies
)


if __name__ == '__main__':
    # --- НАСТРОЙКИ ---
    standards = ['27001', '45001']  # нужные стандарты
    region_code = '77'  # регион клиента
    max_output = 10

    # --- ПУТИ К ФАЙЛАМ ---
    status_file = 'Live_Status.csv'
    region_file = 'files/regions.txt'
    report_file = 'Report.csv'  # если нет — создастся автоматически

    # --- ЗАГРУЗКА И ОБРАБОТКА ---
    companies = build_companies(standards, status_file, region_file)
    filtered = filter_by_standards(companies, standards)
    applications = load_report_and_sync(companies, report_file)

    # --- ПОЛУЧЕНИЕ РАНЖИРОВАННОГО СПИСКА ---
    ranked = rank_companies(filtered, applications, region_code, max_results=max_output)

    # --- ВЫВОД ---
    print("\nРезультаты:")
    for company in ranked:
        print(company)

