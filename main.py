from utils.extract_statements import process_company
from utils.constants import COMPANIES

if __name__ == "__main__":
    for company in COMPANIES:
        print(f"Processing {company['name']}...")
        process_company(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf", company['name'])