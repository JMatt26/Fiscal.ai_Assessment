import pytest
from utils.acquire_pdf import get_pdf_links, download_pdf
from utils.constants import COMPANIES, YEARS
import os

def test_get_pdf_links():
    for company in COMPANIES:
        pdf_links = get_pdf_links(company["annual_reports_url"])
        assert len(pdf_links) > 9, f"No PDF links found for {company['name']} at {company['investor_relations_url']}"
        for pdf_link in pdf_links:
            assert any(year in pdf_link for year in YEARS), f"No {YEARS} in {pdf_link}"

        print("\n")

def test_download_pdf():
    for company in COMPANIES:
        pdf_links = get_pdf_links(company["annual_reports_url"])
        for pdf_link in pdf_links:
            download_pdf(pdf_link, "annual_report_pdfs", company["name"])
            assert os.path.exists(f"annual_report_pdfs/{company['name']}/{pdf_link.split('/')[-1]}"), f"PDF not downloaded for {company['name']} at {pdf_link}"