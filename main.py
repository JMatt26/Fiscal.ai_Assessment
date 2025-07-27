from utils.extract_statements import process_company
from utils.constants import COMPANIES
from utils.post_process import postprocess_excel

if __name__ == "__main__":
    company = COMPANIES[0]
    print(f"Processing {company['name']}...")
    # process_company(f"/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/annual_report_pdfs/Ericsson/NASDAQ_ERIC_2024.pdf", company['name'], "2024")
    postprocess_excel("/Users/jaredmatthews/Programming/Projects/Fiscal.ai_Assessment/outputs/Ericsson.xlsx", "cleaned_outputs", company['name'])