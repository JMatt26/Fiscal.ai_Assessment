from utils.acquire_pdf import download_pdf, get_pdf_links
from utils.extract_statements import process_company, process_company_multi_year
from utils.constants import COMPANIES
from utils.post_process import prune_excel_to_numeric_rows
import os
import re
from collections import OrderedDict

def get_year_to_pdf_map(pdf_paths, base_dir):
    year_to_path = {}

    # Extract year from filename and store in dictionary
    for filename in pdf_paths:
        match = re.search(r'_(\d{4})\.pdf$', filename)
        if match:
            year = int(match.group(1))
            full_path = os.path.join(base_dir, filename)
            year_to_path[year] = os.path.abspath(full_path)

    # Create an ordered dict sorted from most recent to oldest
    sorted_dict = OrderedDict(sorted(year_to_path.items(), key=lambda x: x[0], reverse=True))
    return sorted_dict


if __name__ == "__main__":
    for company in COMPANIES:
        print(f"Processing {company['name']}...")
        pdf_links = get_pdf_links(company['annual_reports_url'])
        for pdf_link in pdf_links:
            download_pdf(pdf_link, "annual_report_pdfs", company['name'])
        company_dir = f"./annual_report_pdfs/{company['name']}"
        pdf_list = os.listdir(company_dir)
        year_pdf_map = get_year_to_pdf_map(pdf_list, company_dir)
        for year, pdf_path in year_pdf_map.items():
            process_company(pdf_path, company['name'], year)
        prune_excel_to_numeric_rows(f"./outputs/{company['name']}.xlsx", f"./cleaned_outputs/{company['name']}.xlsx")

    