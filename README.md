# Fiscal.ai_Assessment
This is the assessment for the Fiscal.ai Data Software Engineer interview process.

## Prerequisites
- Have Python installed
- Have Pip installed

## Installation
- Create a Python virtual environment with ```python -m venv .venv```
- From the project directory, run ```source .venv/bin/activate```
- ```pip install -r requirements.txt```
- From the project directory, run ```touch .env```
  - Within that file, create a ```OPENAI_API_KEY=<>``` variable and put your openai api key value there.

## Use
- ```python main.py```
- To run the unit tests, run ```pytest ./tests``` from the project directory.

## Workflow
This assessment downloads all annual report pdfs from the annualreports.com website for a hardcoded set of companies, found in the ```./utils/constants.py``` file. This is done via webscraping with *requests* and *beautifulsoup*.
- Note: If you wish to run the code with unique companies, simply change the hardcoded data found within that file.

Once downloaded, the pdfs are then processed and their financial data is extracted based on similarity matching and saved to an Excel sheet. This was achieved via *langchain* and *openai*.
Once the initial Excel sheet is made, it is pruned for any values that are non-numeric, to further clean the output.

## Observed Problems
- The code takes roughly 2.5 hours to run in its entirety and process all 30 pdfs. I believe the long runtime stems from the amount of text it processes from each pdf.
- The text extraction section of the code is not refined enough, allowing for too much content to be interpreted as potential financial statements.
- Due to lack of a universal schema amongst annual reports and financial statements, the LLM will miss or pick up too many line items and values.

## Future Iterations
- In order to enhance this code, the data needs to go through several for phases of post-processing, as well as more extensive pre-processing.
  - One possible solution would be to train an LLM with annual reports and the correct schemas, allowing for possible use of said agent on a universal level afterwards.
  - Another solution would be to build a schema for the three financial solutions for all of the data that is wanted universally, then implement some sort of weight system for other line items that are identified, and if they pass a certain *importance weight*, then they are added as to that statement.
