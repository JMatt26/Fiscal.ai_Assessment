import pandas as pd
from openpyxl import load_workbook
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from io import StringIO
import re

from utils.extract_statements import STATEMENT_TYPES, extract_relevant_pages

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def run_llm_on_text(statement_type: str, excel_data: str):
# Prompt for cleaning a financial statement
    prompt_template = PromptTemplate(
        input_variables=["statement_type", "excel_data"],
        template="""
You are a professional financial auditor. Your task is to refine the {statement_type} data given to you as {excel_data}

The data below was automatically extracted and **may include rows that should be removed**.

Your job is to:
1. Filter out any rows that do not appear in an industry standard and typical {statement_type}. 
2. Discard any metrics that are not part of the standard financial statement (e.g., performance ratios, duplicated subtotal rows).
3. Return only valid financial line items with their values as they appear in the official PDF.

### Excel Data (to clean):
{excel_data}

Return your answer as valid JSON object ensuring all items and values are the same as the original data.
Do NOT include markdown or explanations.
"""
    )
    chain = prompt_template | llm
    return chain.invoke({"statement_type": statement_type, "excel_data": excel_data})

def postprocess_excel(pdf_path: str, company_name: str, report_year: str, excel_path: str):
    os.makedirs("cleaned_outputs", exist_ok=True)
    writer = pd.ExcelWriter(f"cleaned_outputs/{company_name}.xlsx", engine="openpyxl")

    for statement_type, keywords in STATEMENT_TYPES.items():
        print(f"Processing {statement_type} for {company_name} {report_year}...")
        data_rows = {}
        try:
            df = pd.read_excel(excel_path, sheet_name=statement_type)
            excel_data_str = df.to_csv(index=False)
            response = run_llm_on_text(statement_type, excel_data_str)
            content = response.content if hasattr(response, "content") else response

            # Clean LLM response
            cleaned_json = re.sub(r"^```(?:json)?\s*|```$", "", content.strip(), flags=re.MULTILINE)

            try: 
                parsed = pd.read_json(StringIO(cleaned_json))
            except ValueError:
                try:
                    # Try interpreting it as a single row of scalar values
                    parsed_dict = eval(cleaned_json)
                    if isinstance(parsed_dict, dict):
                        parsed = pd.DataFrame([parsed_dict])
                    else:
                        raise
                except Exception as inner:
                    print(f"Secondary parse error: {inner}")
                    print("---- INVALID JSON ----")
                    print(cleaned_json)
                    continue
                
            if "Line Item" in parsed.columns and "Value(s)" in parsed.columns:
                # Handle expected schema
                for _, row in parsed.iterrows():
                    item = row["Line Item"]
                    value = row["Value(s)"]
                    data_rows.setdefault(item, {})[report_year] = value
            else:
                # Fallback: treat each column as a line item with single value
                for col in parsed.columns:
                    value = parsed[col].iloc[0] if not parsed[col].isnull().all() else None
                    if value is not None:
                        data_rows.setdefault(col, {})[report_year] = value

            print(f"Data for {statement_type} processed.")

        except Exception as e:
            print(f"Error processing page {statement_type}: {e}")
            print("---- RAW CONTENT ----")
            print(content)

        if data_rows:
            df_sheet = pd.DataFrame.from_dict(data_rows, orient="index").reset_index()
            df_sheet = df_sheet.rename(columns={"index": "Line Item"})
            df_sheet.to_excel(writer, sheet_name=statement_type[:31], index=False)
        else:
            print(f"No data extracted for {statement_type}.")

    writer.close()