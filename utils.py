import os
import re
import json
import requests
import pandas as pd
from urllib.parse import urljoin
from dotenv import load_dotenv

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# Load environment
load_dotenv()

# Load API key
api_key = os.getenv("OPENAI_API_KEY")

# Initialize LLM
CLIENT = OpenAI(openai_api_key=api_key, temperature=0, model_name="gpt-4")

# Constants
years = [str(y) for y in range(2024, 2014, -1)]
STATEMENT_PATTERNS = {
    'income': [r'income statement', r'statement of operations', r'statement of income'],
    'balance': [r'balance sheet', r'statement of financial position'],
    'cashflow': [r'cash flow', r'statement of cash flows']
}
STATEMENT_TYPES = list(STATEMENT_PATTERNS)
SYNONYMS = {
    'revenue': 'total revenue', 'net revenue': 'total revenue', 'sales': 'total revenue',
    'total revenue': 'total revenue', 'cost of goods sold': 'cost of sales', 'cogs': 'cost of sales',
    'cost of sales': 'cost of sales', 'gross profit': 'gross profit', 'operating income': 'operating income',
    'ebit': 'operating income', 'net income': 'net income', 'net income (loss)': 'net income',
    'total assets': 'total assets', 'total liabilities': 'total liabilities', 'total equity': 'total equity',
    'cash flow from operating activities': 'operating cash flow',
    'net cash provided by operating activities': 'operating cash flow',
    'operating cash flow': 'operating cash flow',
    'cash flow from investing activities': 'investing cash flow',
    'net cash used in investing activities': 'investing cash flow',
    'investing cash flow': 'investing cash flow',
    'cash flow from financing activities': 'financing cash flow',
    'net cash provided by financing activities': 'financing cash flow',
    'financing cash flow': 'financing cash flow', 'free cash flow': 'free cash flow'
}

# Companies configuration
tickers = [
    {"name": "Ericsson", "ticker": "ERIC", "annual_reports_url": "https://www.annualreports.com/Company/ericsson"},
    {"name": "Volkswagen", "ticker": "VOW.DE", "annual_reports_url": "https://www.annualreports.com/Company/volkswagen-group"},
    {"name": "LVMH", "ticker": "MC.PA", "annual_reports_url": "https://www.annualreports.com/Company/lvmh"}
]

def normalize_item(name: str) -> str:
    key = name.lower().strip()
    return SYNONYMS.get(key, name)

def get_pdf_links(company_url: str) -> list[str]:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    resp = session.get(company_url, timeout=10)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    year_to_url = {}
    seen = set()
    for a in soup.select("a[onclick*='Annual Report']"):
        m = re.search(r"(20\d{2}) Annual Report", a.get("onclick", ""))
        if m and m.group(1) in years:
            url = session.get(urljoin(company_url, a.get("href")), allow_redirects=True, timeout=10).url
            if url.lower().endswith('.pdf') and url not in seen:
                year_to_url[m.group(1)] = url; seen.add(url)
    for a in soup.select("a[href$='.pdf']"):
        href = a['href']; full = urljoin(company_url, href)
        m = re.search(r"(20\d{2})", href)
        year = m.group(1) if m and m.group(1) in years else None
        if year and full not in seen:
            year_to_url[year] = full; seen.add(full)
    return [year_to_url[y] for y in years if y in year_to_url]

def download_pdf(url: str, output_dir: str, ticker: str) -> str:
    company_dir = os.path.join(output_dir, ticker)
    os.makedirs(company_dir, exist_ok=True)
    filename = os.path.join(company_dir, url.split('/')[-1])
    r = requests.get(url); r.raise_for_status()
    with open(filename, 'wb') as f: f.write(r.content)
    return filename

def process_reports_langchain(pdf_paths: list[str], ticker: str, output_dir: str):
    records = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for pdf in pdf_paths:
        fn = os.path.basename(pdf)
        m = re.search(r"(20\d{2})", fn)
        year = int(m.group(1)) if m else None

        loader = PyPDFLoader(pdf)
        docs = loader.load()
        chunks = splitter.split_documents(docs)

        for stmt in STATEMENT_TYPES:
            tmpl = (
                "You are a financial extractor. Determine if the following context contains the {stmt} statement. "
                "If it does, extract each line item, its value, and its period, returning a JSON array of objects "
                "with keys 'item','value','period'. If not, return an empty JSON array [].\n"
                "Context:\n{context}"
            )
            prompt = PromptTemplate(input_variables=["context"], template=tmpl, partial_variables={"stmt": stmt})
            chain = LLMChain(llm=CLIENT, prompt=prompt)

            for chunk in chunks:
                output = chain.run(context=chunk.page_content)
                try:
                    items = json.loads(output)
                except json.JSONDecodeError:
                    m2 = re.search(r"\[.*\]", output, re.DOTALL)
                    items = json.loads(m2.group(0)) if m2 else []

                for rec in items:
                    records.append({
                        'statement': stmt,
                        'item': normalize_item(rec.get('item', '').strip()),
                        'period': rec.get('period'),
                        'value': rec.get('value'),
                        'reported_year': year
                    })

    df = pd.DataFrame(records)
    df = df.sort_values('reported_year').drop_duplicates(
        subset=['statement','item','period'], keep='last'
    )

    for stmt in STATEMENT_TYPES:
        pivot = df[df['statement'] == stmt].pivot(
            index='item', columns='period', values='value'
        )
        out = os.path.join(output_dir, f"{ticker}_{stmt}_latest.csv")
        pivot.to_csv(out)
        print(f"Saved {out}")

def main(output_dir: str = "reports"):
    for comp in tickers:
        links = get_pdf_links(comp['annual_reports_url'])
        pdfs = [download_pdf(u, output_dir, comp['ticker']) for u in links]
        process_reports_langchain(pdfs, comp['ticker'], output_dir)

if __name__ == "__main__":
    main()



