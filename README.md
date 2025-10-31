# 📊 Piso Patrol — Personal Finance Dashboard

**Cash Cohort** is a comprehensive personal finance analytics app built with **Streamlit**.  
It transforms your raw transaction data — from CSVs or Google Sheets — into an **interactive dashboard** designed to help you not just track your spending, but truly understand your financial habits, set goals, and find new ways to save.

---

## ✨ Key Features

### 🔹 Flexible Data Loading
Import data from:
- A local **CSV file**
- A **public Google Sheet**
- Or use a **sample dataset** to get started instantly.

### 🔹 Intelligent Data Mapping
- Automatically detects standard columns (`Date`, `Amount`, `Category`).
- Includes a powerful **manual mapping interface** for non-standard files.
- Ensures your data aligns perfectly with the app’s schema.

### 🔹 Interactive Data Editor
- Clean, re-categorize, or enrich your transactions after loading.
- Fix typos, change categories (e.g., from *Expense* → *Stash*), or add missed cash purchases.
- Works like an Excel-style grid with full edit and save functionality.

### 🏦 Stashes & Goal Setting
- Define specific **savings goals** (e.g., *Vacation Fund*, *New Car*).
- Track “deposits” re-classified from expenses.
- View **progress bars** and goal attainment metrics per stash.

---

## 📈 Deep-Dive Dashboards

### **Overview**
A high-level command center showing:
- Total income, expenses, stashes, and net savings
- Cumulative charts and financial health trends
- Category-level breakdowns for fast insight

### **Expenses**
- Advanced analytics for spending patterns  
- Automated insights (MoM change, spending pace alerts)  
- Visuals: Daily/weekly/monthly trends, treemap, bubble chart  
- Full searchable transaction log

### **Income**
- Clear summaries of earnings over time  
- Source breakdowns and monthly trends  
- YTD change analysis and distribution charts

### **Stashes**
- Dedicated page for tracking savings goals  
- Displays contributions, average deposit size, and progress toward goals

---

## 🧮 Advanced Analytics

### 🤖 Automated Insights
Get contextual English summaries like:  
> *“Your ‘Family & Friends’ spending was ₱550 this month — a 22 % increase from ₱450 last month.”*

### 🧩 Category Clustering
A mini data-science section using **K-Means clustering** to analyze your spending patterns and group categories into cohorts such as:
- *Large & Fixed*
- *Daily Essentials*
- *Lifestyle Flex*

---

## 🚀 Getting Started

Follow these steps to run **Cash Cohort** locally.

### 1️⃣ Prerequisites
- Python **3.8+**
- **pip** (Python package manager)

### 2️⃣ Installation

Clone this repository:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```
Create a virtual environment (recommended):
```bash
# Mac / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the App

From the project root (the folder containing 1_Home.py):
```bash
streamlit run 1_Home.py
```
Streamlit will automatically open in your default browser.
If not, copy the local URL shown in your terminal (e.g. http://localhost:8501).

## 📦 Project Structure
```bash
your-repo-name/
│
├── 1_Home.py                   # Main welcome page
├── utils.py                    # Shared utility functions (e.g., currency selector)
├── requirements.txt            # Python dependencies
├── data.csv                    # (Optional) Sample data file
│
└── pages/                      # App sub-pages
    ├── 2_Data_Mapping.py
    ├── 3_Overview.py
    ├── 4_Expenses.py
    ├── 5_Income.py
    ├── 6_Stashes.py
    └── 7_Category_Cluster_Analysis.py
```

## 👤 Author

**Arvin Escolano**  
Senior Data Analyst | Data Visualization & Automation Enthusiast  

- 🌙 Based in Manila — thriving on night-shift creativity  
- 🧠 Passionate about turning data into actionable insights through clean design and storytelling  
- 💼 Skilled in Python, SQL, Streamlit, and data automation workflows  

📫 **Connect with me:**  
[💼 LinkedIn](https://linkedin.com/in/arvin-jay-escolano) • [🐙 GitHub](https://github.com/the-arvin) • [✉️ Email](mailto:ajescolano@gmail.com)
