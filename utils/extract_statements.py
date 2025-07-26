import os
import re
import pdfplumber
import pandas as pd
from utils.constants import COMPANIES, YEARS
from dotenv import load_dotenv
# from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from io import StringIO

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

STATEMENT_TYPES = {
    "Income Statement": ["income statement", "statement of operations"],
    "Balance Sheet": ["balance sheet", "financial position"],
    "Cash Flow Statement": ["cash flow", "statement of cash flows"]
}

def has_table(page):
    return bool(page.extract_tables())

def extract_relevant_pages(pdf_path: str, keywords: list[str]) -> list[tuple[int, str]]:
    """
    Extract text from a PDF file by matching keywords and filtering out irrelevant or non-tabular pages.
    """
    matches = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if any(kw.lower() in text.lower() for kw in keywords):
                if has_table(page):
                    matches.append((i + 1, text))
    return matches

def run_llm_on_text(statement_type: str, text_chunk: str):
    """
    Run the LLM with a strict table-focused financial prompt.
    """
    prompt_template = PromptTemplate(
        input_variables=["statement_type", "text_chunk"],
        template="""
You are a financial analyst. Extract only the structured numerical table from the following financial report text.

Focus specifically on a {statement_type}. Return the result strictly as **valid JSON** in this format:
[
  {{ "Line Item": "...", "Value(s)": "..." }},
  ...
]

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
    os.makedirs("outputs", exist_ok=True)
    writer = pd.ExcelWriter(f"outputs/{company_name}.xlsx", engine="openpyxl")

    for statement_type, keywords in STATEMENT_TYPES.items():
        print(f"Processing {statement_type} for {company_name} {report_year}...")

        pages = extract_relevant_pages(pdf_path, keywords)
        line_item_map = {}

        for page_num, text in pages:
            try:
                response = run_llm_on_text(statement_type, text)
                content = response.content if hasattr(response, "content") else response

                # Clean LLM response: remove ```json blocks if present
                cleaned_json = re.sub(r"^```(?:json)?\s*|```$", "", content.strip(), flags=re.MULTILINE)
                df = pd.read_json(StringIO(cleaned_json))

                for _, row in df.iterrows():
                    item = row["Line Item"]
                    value = row["Value(s)"]
                    line_item_map[item] = value

                print(f"Page {page_num} processed.")

            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                print("---- RAW CLEANED JSON ----")
                print(content)

        if line_item_map:
            # One column per report, like "2024"
            df_sheet = pd.DataFrame.from_dict(line_item_map, orient="index", columns=[report_year])
            df_sheet.index.name = "Line Item"
            df_sheet.reset_index(inplace=True)

            # Trim sheet name to 31 characters max (Excel limit)
            df_sheet.to_excel(writer, sheet_name=statement_type[:31], index=False)
        else:
            print(f"No data extracted for {statement_type}.")

    writer.close()
