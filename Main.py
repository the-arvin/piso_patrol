import streamlit as st
from utils import add_currency_selector # Import the new function

st.set_page_config(
    page_title="Budget App Home",
    page_icon="🏠",
    layout="wide"
)

def home_page():
    """
    This is the main welcome page of the app.
    """
    add_currency_selector() # Add the currency selector to the sidebar

    st.title("Welcome to Your Personal Budgeting App! 👋")
    st.markdown("---")

    st.header("🚀 Let's Get Your Finances Sorted!")
    st.markdown("""
    This application is designed to help you take control of your financial life. 
    By uploading your transaction data, you can get a clear, visual understanding of where your money comes from, where it goes, and how you're tracking toward your savings goals.
    """)

    st.subheader("Here's Your Journey:")
    
    st.markdown("""
    1.  **🗺️ Data Mapping:** This is your "Control Center" and the most important first step. 
        * Go to the **'Data Mapping'** page from the sidebar.
        * The app will automatically find and load your `.csv` file.
        * It will try to process your data automatically. If it can't, you can use the manual tools to map your columns.
        * **Crucially:** This is where you can **edit transactions**, **re-classify data** (e.g., as 'Stash'), and **set up your savings goals, complete with emojis!**
    
    2.  **📊 Overview:** Once your data is mapped, this is your "Command Center".
        * See your total **Income**, **Expenses**, and **Stashed** amounts in high-level cards.
        * Track your cumulative financial health over time.
        * Get a quick breakdown of your main spending categories.

    3.  **💸 Expenses & 💰 Income:** Dive deeper into the details.
        * These pages provide detailed charts and tables for all your spending and earning.
        * Analyze your spending habits by day, week, month, and category.

    4.  **🏦 Stashes:** This is your goal-tracking dashboard.
        * This page automatically pulls the goals you defined in **'Data Mapping'**.
        * See your progress for each savings goal in a clear, card-based layout.

    """)
    
    st.info("To get started, please navigate to the **'Data Mapping'** page in the sidebar. ➡️", icon="💡")

if __name__ == "__main__":
    home_page()

