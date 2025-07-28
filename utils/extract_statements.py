import os
import re
import json
import pdfplumber
import pandas as pd
from utils.constants import STATEMENT_TYPES
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from io import StringIO

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def has_table(page):
    return bool(page.extract_tables())

def extract_relevant_pages(pdf_path: str, keywords: list[str]) -> list[tuple[int, str]]:
    """
    Extract text from a PDF file by matching keywords and filtering out irrelevant or non-tabular pages.

    Args:
        pdf_path: The path to the pdf file.
        keywords: A list of keywords to search for in the pdf.

    Returns:
        A list of tuples, where each tuple contains the page number and the text of the page.
    """

    matches = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if any(kw.lower() in text.lower() for kw in keywords):
                if has_table(page):
                    matches.append((i + 1, text))
    return matches

def extract_relevant_tables(pdf_path: str, keywords: list[str]) -> list[tuple[int, list]]:
    """
    Extract tables from PDF pages containing financial keywords.

    Args:
        pdf_path: The path to the pdf file.
        keywords: A list of keywords to search for in the pdf.

    Returns:
        A list of tuples, where each tuple contains the page number and the tables on the page.
    """

    matches = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if any(kw.lower() in text.lower() for kw in keywords):
                tables = page.extract_tables()
                for table in tables:
                    if table:  # non-empty
                        matches.append((i + 1, table))
    return matches

def run_llm_on_text(statement_type: str, text_chunk: str, year: str):
    """
    Run the LLM with a strict table-focused financial prompt.

    Args:
        statement_type: The type of statement to extract.
        text_chunk: The text to extract the statement from.
        year: The year of the statement.

    Returns:
        A string of the extracted statement in JSON format.
    """

    prompt_template = PromptTemplate(
        input_variables=["statement_type", "text_chunk"],
        template=f"""
You are a financial analyst. Given an annual report for the {year} year, extract all information, items and values, from the {statement_type}. 
Return the result strictly as **valid JSON**. 
Ensure that one line item has only one value, and that value is for the {year} year.
DO NOT include markdown, explanations, or commentary. Only extract relevant numerical data rows.
------------------
{text_chunk}
"""
    )

    chain = prompt_template | llm
    return chain.invoke({
        "statement_type": statement_type,
        "text_chunk": text_chunk
    })


def process_company(pdf_path: str, company_name: str, report_year: str):
    """
    Process a single PDF file for a specific year and save the results to an Excel file.

    Args:
        pdf_path: The path to the pdf file.
        company_name: The name of the company.
        report_year: The year of the report.
    """

    os.makedirs("outputs", exist_ok=True)
    excel_path = f"outputs/{company_name}.xlsx"

    if os.path.exists(excel_path):
        writer = pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="overlay")
    else:
        writer = pd.ExcelWriter(excel_path, engine="openpyxl")

    for statement_type, keywords in STATEMENT_TYPES.items():
        print(f"Processing {statement_type} for {company_name} {report_year}...")

        pages = extract_relevant_pages(pdf_path, keywords)
        data_rows = {}

        for page_num, text in pages:
            try:
                response = run_llm_on_text(statement_type, text, report_year)
                content = response.content if hasattr(response, "content") else response
                cleaned_json = re.sub(r"^```(?:json)?\s*|```$", "", content.strip(), flags=re.MULTILINE)

                try:
                    parsed = pd.read_json(StringIO(cleaned_json))
                except ValueError:
                    try:
                        parsed_dict = eval(cleaned_json)
                        parsed = pd.DataFrame([parsed_dict]) if isinstance(parsed_dict, dict) else None
                        if parsed is None:
                            raise
                    except Exception as inner:
                        print(f"Secondary parse error: {inner}")
                        print("---- INVALID JSON ----")
                        print(cleaned_json)
                        continue

                if parsed is None:
                    continue

                if "Line Item" in parsed.columns and "Value(s)" in parsed.columns:
                    for _, row in parsed.iterrows():
                        item = row["Line Item"]
                        value = row["Value(s)"]
                        if isinstance(value, dict):
                            for year, v in value.items():
                                data_rows.setdefault(item, {})[year] = v
                        else:
                            data_rows.setdefault(item, {})[report_year] = value
                else:
                    for col in parsed.columns:
                        value = parsed[col].iloc[0] if not parsed[col].isnull().all() else None
                        if value is not None:
                            data_rows.setdefault(col, {})[report_year] = value

                print(f"Page {page_num} processed.")

            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                print("---- RAW CONTENT ----")
                print(content)

        if data_rows:
            new_df = pd.DataFrame.from_dict(data_rows, orient="index").reset_index()
            new_df = new_df.rename(columns={"index": "Line Item"})

            # Read existing sheet if it exists
            try:
                existing_df = pd.read_excel(excel_path, sheet_name=statement_type[:31])
                # Preserve original row order from existing_df
                existing_df["__order"] = range(len(existing_df))

                merged_df = pd.merge(existing_df, new_df, on="Line Item", how="outer")

                # Restore order if possible
                if "__order" in merged_df.columns:
                    merged_df = merged_df.sort_values("__order").drop(columns="__order")
            except FileNotFoundError:
                merged_df = new_df
            except ValueError:
                # Sheet doesn't exist yet
                merged_df = new_df

            merged_df.to_excel(writer, sheet_name=statement_type[:31], index=False)
        else:
            print(f"No data extracted for {statement_type}.")

    writer.close()


def process_company_multi_year(pdf_paths_in_order: dict[str, str], company_name: str):
    os.makedirs("outputs", exist_ok=True)
    statement_dataframes: dict[str, pd.DataFrame] = {}

    for report_year, pdf_path in pdf_paths_in_order.items():
        print(f"Processing {company_name} {report_year}...")

        for statement_type, keywords in STATEMENT_TYPES.items():
            print(f"  → {statement_type}")
            pages = extract_relevant_pages(pdf_path, keywords)
            data_rows = {}

            for page_num, text in pages:
                try:
                    response = run_llm_on_text(statement_type, text, report_year)
                    content = response.content if hasattr(response, "content") else response
                    cleaned_json = re.sub(r"^```(?:json)?\s*|```$", "", content.strip(), flags=re.MULTILINE)

                    try:
                        parsed = pd.read_json(StringIO(cleaned_json))
                    except ValueError:
                        parsed_dict = json.loads(cleaned_json)
                        if isinstance(parsed_dict, dict):
                            parsed = pd.DataFrame([parsed_dict])
                        else:
                            raise

                    if "Line Item" in parsed.columns and "Value(s)" in parsed.columns:
                        for _, row in parsed.iterrows():
                            item = row["Line Item"]
                            value = row["Value(s)"]
                            data_rows.setdefault(item, {})[report_year] = value
                    else:
                        for col in parsed.columns:
                            value = parsed[col].iloc[0] if not parsed[col].isnull().all() else None
                            if value is not None:
                                data_rows.setdefault(col, {})[report_year] = value

                    print(f"    ✓ Page {page_num} processed.")

                except Exception as e:
                    print(f"    ✗ Error processing page {page_num}: {e}")
                    print("    RAW LLM Output:\n", content)

            if data_rows:
                # Build DataFrame with a single column (report_year) and Line Item as index
                df_new = pd.DataFrame.from_dict(data_rows, orient="index", columns=[report_year])
                df_new.index.name = "Line Item"
                
                if statement_type not in statement_dataframes:
                    statement_dataframes[statement_type] = df_new
                else:
                    # Join without sorting, just stacking columns in order
                    statement_dataframes[statement_type] = statement_dataframes[statement_type].join(
                        df_new, how="outer"
                    )

    # Write combined data per statement
    writer = pd.ExcelWriter(f"outputs/{company_name}.xlsx", engine="openpyxl")
    for sheet_name, df in statement_dataframes.items():
        df.reset_index(inplace=True)
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    writer.close()