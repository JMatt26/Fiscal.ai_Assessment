import pandas as pd
from openpyxl import load_workbook
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from io import StringIO

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Prompt for cleaning a financial statement
prompt_template = PromptTemplate(
    input_variables=["statement_type", "csv_data"],
    template="""
You are a financial analyst.

The following CSV contains a raw extracted table for a company's {statement_type}. Clean the table by:
- Keeping only financially relevant rows (e.g., Revenue, Operating Profit, Net Income, Assets, Liabilities, Cash Flow) that adhere to industry standards.
- Removing empty or meaningless rows (e.g., "n/a", dashes, subtotals without labels).
- Keeping the original years and numeric values intact.
- Correct any cluttered cells by splitting multiple values into separate columns, aligning with the data's respective year.

Return the cleaned result strictly as a valid CSV. Do not add comments or formatting outside the CSV.
------------------
{csv_data}
"""
)

def clean_sheet(df: pd.DataFrame, statement_type: str) -> pd.DataFrame:
    csv_data = df.to_csv(index=False)
    chain = prompt_template | llm
    response = chain.invoke({"statement_type": statement_type, "csv_data": csv_data})
    cleaned_csv = response.content.strip("`").strip()
    return pd.read_csv(StringIO(cleaned_csv))

def postprocess_excel(input_path: str, output_dir: str, company_name: str):
    # Load Excel file
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(input_path)
    writer = pd.ExcelWriter(f"{output_dir}/{company_name}.xlsx", engine="openpyxl")

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            print(f"Cleaning sheet: {sheet_name}")
            cleaned_df = clean_sheet(df, sheet_name)
            cleaned_df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            print(f"Error processing sheet {sheet_name}: {e}")

    writer.close()
    print(f"Cleaned Excel saved to: {output_dir}/{company_name}.xlsx")