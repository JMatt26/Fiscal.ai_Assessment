from utils.extract_statements import process_company
from utils.constants import COMPANIES
from utils.post_process import postprocess_excel
from utils.extract_schema import find_statement_schema
import os
import re

if __name__ == "__main__":
    company = COMPANIES[0]
    print(f"Processing {company['name']}...")
    files = os.listdir("/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson")
    for file in files:
        abs_file_path = os.path.abspath(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/{file}")
        # Attempt to extract the year from the filename (e.g., ..._2024.pdf)
        match = re.search(r'(\d{4})', file)
        year = match.group(1) if match else "Unknown"
        print(year)
        print(file)
        process_company(abs_file_path, company['name'], year)
    # postprocess_excel(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf", company['name'], "2024", f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/outputs/Ericsson_og.xlsx")
    # find_statement_schema(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf", "Income Statement", "2024")