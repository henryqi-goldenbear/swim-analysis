Swim Performance Data Pipeline & Analysis
An automated data extraction and analysis suite built to scrape, process, and compare competitive swimming data from SwimCloud and SwimPhone. This project demonstrates full-stack data engineering principles, from raw HTML parsing to statistical insights using pandas.

🚀 Features
Multi-Source Scraping: Robust extraction logic for event orders, psych sheets, and prelim results using BeautifulSoup4.

Data Normalization: A custom transformation engine that converts varied time formats (e.g., 2:22.66 or 52.34) into floating-point seconds for mathematical comparison.

Predictive Analytics: Calculates the "Seed vs. Prelim" delta to identify performance trends across different swim meets.

Automated Reporting: Generates descriptive statistics (df.describe()) to provide immediate high-level insights into meet-wide performance.

🛠️ Tech Stack
Language: Python 3.x

Libraries: Requests (Networking), BeautifulSoup4 (Parsing), Pandas (Data Modeling)

Development Tools: AI-accelerated coding (GitHub Copilot), Version Control (Git)

📈 System Design
The project follows a modular service-oriented approach:

Request Layer: Handles headers and user-agents to ensure reliable connection to sports databases.

Extraction Layer: Modular functions (get_psych_table, get_prelims_table) isolate parsing logic.

Modeling Layer: Data is structured into DataFrames, allowing for complex joins and time-series analysis.

🧪 Future Improvements (Production Readiness)
To align with high-growth fintech standards, I am currently working on:

Unit Testing: Implementing pytest to validate scraper reliability against schema changes.

Containerization: Wrapping the pipeline in Docker for consistent deployment in AWS environments.

ML Integration: Using scikit-learn to predict qualifying "cut" times based on historical drop-rates.
