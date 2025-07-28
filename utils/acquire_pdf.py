import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict
import os
from utils.constants import YEARS

def get_pdf_links(company_url: str) -> List[str]:
    """
    Get the PDF links for a company's annual reports.

    Args: 
        company_url: The url of the company's annual reports page.

    Returns:
        A list of annual report urls from 2024 to 2015.
    """

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


def download_pdf(url: str, output_dir: str, company_name: str):
    """
    Download a pdf from a url to a local directory.

    Args:
        url: The url of the pdf to download.
        output_dir: The directory to save the pdf to.
        company_name: The name of the company whose pdf is being downloaded.

    Returns:
        The path to the downloaded pdf.
    """
    
    company_dir = os.path.join(output_dir, company_name)
    os.makedirs(company_dir, exist_ok=True)
    filename = os.path.join(company_dir, url.split("/")[-1])
    resp = requests.get(url)
    resp.raise_for_status()
    with open(filename, "wb") as f:
        f.write(resp.content)
    return filename

