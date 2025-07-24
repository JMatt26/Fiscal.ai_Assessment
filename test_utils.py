import pytest
from utils import get_pdf_links
from utils import COMPANIES

YEARS = [str(y) for y in range(2024, 2013, -1)]

def test_get_pdf_links():
    for company in COMPANIES:
        pdf_links = get_pdf_links(company["annual_reports_url"])
        assert len(pdf_links) > 9, f"No PDF links found for {company['name']} at {company['investor_relations_url']}"
        for pdf_link in pdf_links:
            assert any(year in pdf_link for year in YEARS), f"No {YEARS} in {pdf_link}"

        print("\n")