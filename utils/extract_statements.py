import os
import re
import pdfplumber
import pandas as pd
from utils.constants import COMPANIES, YEARS
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
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


def extract_text_by_keywords(pdf_path: str, keywords: list[str]) -> list[tuple[int, str]]:
    """
    Extract text from a PDF file by matching keywords.
    """
    matches = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if any(kw.lower() in text.lower() for kw in keywords):
                matches.append((i+1, text))
    return matches

def run_llm_on_text(statement_type: str, text_chunk):
    """
    Run the LLM on a text chunk to extract the statements.
    """
    prompt = ChatPromptTemplate.from_template(
        f"""Below is a page from a {statement_type}. Extract a clean, structured table with all rows and columns, as JSON with keys: "Line Item" and "Value(s)".
TEXT: {text_chunk}
"""
    )
    chain = prompt | llm
    return chain.invoke({"statement_type": statement_type, "text_chunk": text_chunk})


def process_company(pdf_path, company_name):
    writer = pd.ExcelWriter(f"outputs/{company_name}.xlsx")

    for statement_type, keywords in STATEMENT_TYPES.items():
        print(f"Processing {statement_type}...")
        pages = extract_text_by_keywords(pdf_path, keywords)
        rows = []

        for i, (page_num, text) in enumerate(pages):
            response = run_llm_on_text(statement_type, text)
            try:
                content = response.content if hasattr(response, "content") else response
                cleaned_json = re.sub(r"^```(?:json)?\s*|```$", "", content.strip(), flags=re.MULTILINE)
                df = pd.read_json(StringIO(cleaned_json))
                df["Page"] = page_num
                rows.append(df)
                print(f"Processed page {page_num}")
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                print("----- RAW CLEANED JSON -----")
                print(cleaned_json)
        
        if rows:
            full_df = pd.concat(rows)
            full_df.to_excel(writer, sheet_name=statement_type, index=False)
        else:
            print(f"No {statement_type} found in {pdf_path}")
    
    writer.close()
