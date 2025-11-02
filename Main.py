import streamlit as st
from utils import add_currency_selector

st.set_page_config(
    page_title="Piso Patrol - Home",
    page_icon="🏠",
    layout="wide"
)

def main_page():
    add_currency_selector() # Add the currency selector to the sidebar
    
    st.title("Welcome to Piso Patrol! 👮‍♂️💰")
    st.markdown("Your all-in-one financial dashboard for tracking, analyzing, and forecasting your personal finances.")
    st.markdown("---")

    st.header("How to Use This App")
    st.markdown("Follow these steps to get the most out of your data.")

    # Step 1: Data Mapping
    with st.expander("Step 1: 🗺️ Data Mapping", expanded=False):
        st.markdown("""
        This is the most crucial step. All your analysis depends on getting your data in and setting it up correctly.
        
        **Key Features:**
        * **Load Your Way:** Load data from a CSV file, a public Google Sheet, or use our built-in Sample Data.
        * **Smart Mapping:** Automatically detects standard columns (`Date`, `Amount`, `Category`, `Subcategory`) or lets you map them manually.
        * **Live Data Editor:** Use the `st.data_editor` to fix typos, add missing cash transactions, or re-classify items on the fly.
        * **Define Your Goals:** This is where you tell the app which `Subcategories` to treat as savings goals (e.g., "Vacation Fund") and set your target amounts and emojis.
        """)
        st.page_link("pages/1_📑_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")

    # Step 2: Overview
    with st.expander("Step 2: 📊 Overview", expanded=False):
        st.markdown("""
        Get a high-level "command center" view of your entire financial picture.
        
        **Key Features:**
        * **Global Date Filter:** Use the sidebar to select a date range that applies to all pages.
        * **At-a-Glance KPIs:** See your `Total Income`, `Total Expenses`, `Total Stashed`, and `Total Savings` in the selected period.
        * **Cumulative Trends:** Watch how your finances grow over time with a cumulative area chart.
        * **Granular Filters:** Filter the dashboard by Accounts, Categories, and Subcategories.
        * **Breakdown Charts:** Instantly see your spending and income breakdowns by `Subcategory` in clear pie charts.
        """)
        st.page_link("pages/2_📊_Overview.py", label="Go to Overview", icon="📊")

    # Step 3: Expenses
    with st.expander("Step 3: 💸 Expenses", expanded=False):
        st.markdown("""
        Dive deep into your spending habits with the most powerful page in the app.
        
        **Key Features:**
        * **Dual-Level Analysis:** Use the toggles to switch your analysis granularity between `Category` and `Subcategory`.
        * **Automated Insights:** Get dynamic reports comparing your selected month's spending to the previous month and your Year-to-Date (YTD) average.
        * **Hierarchical Treemap:** Visually understand your spending with a treemap that lets you drill down from `Category` into `Subcategory`.
        * **Habit Analysis:** Use the Bubble Chart and summary tables to find patterns (e.g., high-frequency, low-cost spending vs. low-frequency, high-cost purchases).
        * **Detailed Transaction Table:** A fully filterable table to find any specific transaction.
        """)
        st.page_link("pages/3_💵_Expenses.py", label="Go to Expenses", icon="💸")

    # Step 4: Income
    with st.expander("Step 4: 💰 Income", expanded=False):
        st.markdown("""
        Track and verify your income streams.
        
        **Key Features:**
        * **YTD Insights:** Compare any month's income against the first month of the year and your YTD average to track your growth.
        * **Sunburst Chart:** See a hierarchical breakdown of your income sources by `Category` and `Subcategory`.
        * **Monthly Trend:** A stacked bar chart shows your total income per month, broken down by `Subcategory`.
        * **Detailed Transaction Table:** A filterable table to verify all your income events.
        """)
        st.page_link("pages/4_💰_Income.py", label="Go to Income", icon="💰")

    # Step 5: Stashes
    with st.expander("Step 5: 🏦 Stashes", expanded=False):
        st.markdown("""
        This is where your saving goals come to life.
        
        **Key Features:**
        * **Goal Forecasting:** Automatically calculates your **Estimated Goal Date** based on your average *monthly* savings rate.
        * **Progress Tracking:** The progress bar shows your *total, all-time* savings toward your goal.
        * **Period Metrics:** The cards show you how much you contributed *within the selected date range*.
        * **Goal Editor:** You can define and update your stash goals, targets, and emojis directly on this page or on the Data Mapping page.
        """)
        st.page_link("pages/5_🏦_Stashes.py", label="Go to Stashes", icon="🏦")

    # Retain the Pro Tip section
    st.markdown("---")
    with st.expander("🤖 Pro Tip: Automate Your Data Entry with AI", expanded=True):
        st.markdown("""
        Tired of manual data entry? You can automate this entire process!
        
        1.  **Use an AI Assistant:** Use an AI like ChatGPT or Gemini with the `AI_ASSISTANT_PROMPT.md` file found in this app's [GitHub repository](https://github.com/your-username/your-repo/blob/main/AI_ASSISTANT_PROMPT.md).
        2.  **Log Transactions via Chat:** Simply send texts or upload receipts to your AI. It will parse them and format them correctly.
        3.  **Export to Google Sheets:** When you're ready, tell your AI "export". It will give you a text block to copy.
        4.  **Paste into Google Sheets:** Paste the data into the Google Sheet you've linked to this app.
        5.  **Refresh & Analyze:** Come back to this app, reload the data on the 'Data Mapping' page, and all your new transactions will be ready for analysis!
        """)

if __name__ == "__main__":
    main_page()
