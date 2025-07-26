# from utils import COMPANIES, process_reports_for_company
# import os

# OUTPUT_DIR = 'reports'

# if __name__ == "__main__":
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     for company in COMPANIES:
#         print(f"Processing {company['name']}...")
#         try:
#             output_dir = os.path.join(OUTPUT_DIR, company['name'])
#             process_reports_for_company(company, output_dir)
#         except Exception as e:
#             print(f"Error processing {company['name']}: {e}")
#     print("All companies processed.")
