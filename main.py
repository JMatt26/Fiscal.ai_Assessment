from utils.extract_statements import process_company, process_company_multi_year
from utils.constants import COMPANIES
from utils.post_process import prune_excel_to_numeric_rows
import os
import re

if __name__ == "__main__":
    company = COMPANIES[0]
    print(f"Processing {company['name']}...")
    # files = os.listdir("/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson")
    # for file in files:
    #     abs_file_path = os.path.abspath(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/{file}")
    #     # Attempt to extract the year from the filename (e.g., ..._2024.pdf)
    #     match = re.search(r'(\d{4})', file)
    #     year = match.group(1) if match else "Unknown"
    #     print(year)
    #     print(file)
    #     process_company(abs_file_path, company['name'], year)
    # # postprocess_excel(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf", company['name'], "2024", f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/outputs/Ericsson_og.xlsx")
    # # find_statement_schema(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf", "Income Statement", "2024")

    # list_of_pdfs = {
    #     "2024": "/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf",
    #     "2023": "/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2023.pdf",
    #     # "2022": "/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2022.pdf"
    # }
    
    # # process_company_multi_year(list_of_pdfs, company['name'])
    # for year, pdf_path in list_of_pdfs.items():
    #     process_company(pdf_path, company['name'], year)


    prune_excel_to_numeric_rows("/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/outputs/Ericsson.xlsx", "/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/cleaned_outputs/Ericsson_cleaned.xlsx")

    