import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict

COMPANIES = [
    {
        "name": "Ericsson",
        "ticker": "ERIC",
        "investor_relations_url": "https://www.ericsson.com/en/investors",
        "annual_reports_url": "https://www.annualreports.com/Company/ericsson",
    },
    {
        "name": "Volkswagen",
        "ticker": "VOW.DE",
        "investor_relations_url": "https://www.volkswagen-group.com/en/financial-reports-18134?query=#",
        "annual_reports_url": "https://www.annualreports.com/Company/volkswagen-group",
    },
    {
        "name": "LVMH",
        "ticker": "MC.PA",
        "investor_relations_url": "https://www.lvmh.com/en/investors",
        "annual_reports_url": "https://www.annualreports.com/Company/lvmh",
    }
]

YEARS = [str(y) for y in range(2024, 2014, -1)]

def get_pdf_links(company_url: str) -> List[str]:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    resp = session.get(company_url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")

    year_to_url: Dict[str, str] = {}
    seen_urls: set[str] = set()
    for a in soup.select("a[onclick*='Annual Report']"):
        onclick = a.get("onclick", "")
        m = re.search(r"(\d{4})\s+Annual Report", onclick)
        if not m:
            continue
        year = m.group(1)
        if year not in YEARS:
            continue

        href = a.get("href")
        if not href:
            continue
        click_url = urljoin(company_url, href)
        pdf_resp = session.get(click_url, allow_redirects=True, timeout=10)
        final_pdf = pdf_resp.url
        if final_pdf.lower().endswith(".pdf") and final_pdf not in seen_urls:
            year_to_url[year] = final_pdf
            seen_urls.add(final_pdf)
            print(f"Found PDF link for year {year}: {final_pdf}")

    for a in soup.select("a[href$='.pdf']"):
        href = a["href"]
        full = urljoin(company_url, href)
        # infer year from URL or from the surrounding title
        m = re.search(r"(20\d{2})", href)
        if m:
            year = m.group(1)
        else:
            # fallback: look for a sibling title div
            parent = a.find_parent("div", class_="table-item")
            if parent:
                title_div = parent.select_one(".table-item__title")
                m2 = re.search(r"(20\d{2})", title_div.text) if title_div else None
                year = m2.group(1) if m2 else None
            else:
                year = None

        if year in YEARS and full not in seen_urls:
            year_to_url[year] = full
            seen_urls.add(full)
            print(f"Found PDF link for year {year}: {full}")

    
    return [year_to_url[yr] for yr in YEARS if yr in year_to_url]
