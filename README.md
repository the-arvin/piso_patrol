📊 Piso Patrol - Personal Finance Dashboard

Welcome to Cash Cohort, a comprehensive personal finance analytics app built with Streamlit. This tool transforms your raw transaction data from CSVs or Google Sheets into a powerful, interactive dashboard. It's designed to help you not just track your spending, but truly understand your financial habits, set goals, and find new ways to save.

✨ Key Features

Flexible Data Loading: Import your data from a CSV file or directly from a public Google Sheet. A sample dataset is also included to get you started instantly.

Intelligent Data Mapping: The app automatically detects standard columns (Date, Amount, Category). For non-standard files, it provides a powerful UI to map your columns to the app's schema.

Interactive Data Editor: Clean your data after loading. Fix typos, re-categorize transactions (e.g., from Expense to Stash), or add missed cash purchases using an Excel-like data editor.

🏦 Stash & Goal Setting: Define specific savings goals (e.g., "Vacation Fund," "New Car"). The app will track your "deposits" (re-categorized expenses) and show your progress toward each goal with clear attainment bars.

Deep Dive Dashboards:

Overview: A high-level command center showing your total income, expenses, stashes, and net savings with cumulative charts and category breakdowns.

Expenses: A detailed analysis of your spending with automated insights (MoM changes, spending pace alerts), trend analysis (daily, weekly, monthly), a treemap, a bubble chart, and a full transaction log.

Income: A clear summary of your earnings with YTD change analysis, income source breakdowns, and monthly trends.

Stashes: A dedicated page to track your savings goals, showing your progress, total contributions, and goal attainment.

Advanced Analytics:

Automated Insights: Get plain-English insights like, "Your 'Family & Friends' spending was $550 this month, a 22% increase from $450 last month."

Category Clustering: A special data science section that uses K-Means clustering to analyze your spending habits and group your categories into "cohorts" (e.g., "Large & Fixed," "Daily Essentials").

🚀 Getting Started

Follow these steps to get the app running on your local machine.

1. Prerequisites

Python 3.8+

pip (Python package installer)

2. Installation

Clone the repository:

git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name



Create a virtual environment (Recommended):

# For Mac/Linux
python3 -m venv .venv
source .venv/bin/activate

# For Windows
python -m venv .venv
.\.venv\Scripts\activate



Install the required libraries:
The project includes a requirements.txt file with all necessary packages.

pip install -r requirements.txt



3. Running the App

Run the Streamlit app:
Make sure you are in the root directory of the project (the one containing 1_Home.py).

streamlit run 1_Home.py



View in your browser:
Streamlit will automatically open a new tab in your default browser. If it doesn't, your terminal will show a local URL (e.g., http://localhost:8501) that you can open.

4. How to Use

Start on the "Data Mapping" page: This is the first and most important step.

Load Your Data: Choose to upload a CSV, paste a Google Sheet link, or load the sample data.

Process Data: The app will try to auto-process your data. If it fails, or if you want to make changes, use the "Manual Column Mapping" tools and click "Process & Save".

Define Stashes: Use "Step 4" on the Data Mapping page to set your savings goals.

Explore!: You're all set. Navigate to the Overview, Expenses, Income, Stashes, and Cluster Analysis pages to explore your financial world.

📦 Project Structure

your-repo-name/
│
├── 1_Home.py             # The main welcome page
├── utils.py              # Shared utility functions (e.g., currency selector)
├── requirements.txt      # All Python package dependencies
├── data.csv              # (Optional) Your local data file
│
└── pages/                # Contains all the sub-pages of the app
    ├── 2_Data_Mapping.py
    ├── 3_Overview.py
    ├── 4_Expenses.py
    ├── 5_Income.py
    ├── 6_Stashes.py
    └── 7_Category_Cluster_Analysis.py

