import streamlit as st
from utils import add_currency_selector

st.set_page_config(
    page_title="Piso Patrol - Station 1",
    page_icon="🏠",
    layout="wide"
)

def home_page():
    """
    Main home/welcome page for the app.
    """
    add_currency_selector()
    
    st.title("Welcome to Piso Patrol! 💸")
    st.header("Your Personal Financial Dashboard & Analyst")
    st.markdown("---")

    st.markdown(
        """
        This app is your new command center for understanding exactly where your money goes. 
        It's designed to take your raw transaction data and turn it into clear, actionable insights. 
        
        No more guessing, just clear data.
        """
    )
    
    st.subheader("🚀 How to Use This App")
    st.markdown("Follow these simple steps to get started:")

    with st.expander("Step 1: 🗺️ Go to the Data Mapping Page", expanded=False):
        st.markdown(
            """
            * This is the most important step! Here you will load your financial data.
            * You can upload a `.csv` file, link a public Google Sheet, or load our sample data to get started.
            * The app will try to auto-detect your columns (`Date`, `Amount`, `Category`).
            * You can then use the **Data Editor** to fix typos, add missing transactions, or re-classify items.
            """
        )

    with st.expander("Step 2: 🏦 Define Your Stashes (Savings Goals)", expanded=False):
        st.markdown(
            """
            * Still on the `Data Mapping` page, you can designate specific expense categories (like "Vacation Fund" or "New Car") as **Stashes**.
            * Set a goal amount and assign a fun emoji for each stash.
            """
        )

    with st.expander("Step 3: 📊 Explore Your Overview", expanded=False):
        st.markdown(
            """
            * Get a high-level snapshot of your financial health.
            * See your total Income, Expenses, and Stash contributions in one place.
            * Track your cumulative savings over time with our interactive chart.
            """
        )

    with st.expander("Step 4: 💸 Dive into Expenses & Income", expanded=False):
        st.markdown(
            """
            * Get a detailed breakdown of your spending habits with automated insights.
            * Analyze your spending by category, day of the week, or month.
            * Confirm your income streams and track their performance over the year.
            """
        )

    with st.expander("Step 5: 🏆 Track Your Stashes", expanded=False):
        st.markdown(
            """
            * See all your savings goals as interactive cards.
            * Watch your progress bars fill up as you get closer to hitting your targets!
            """
        )

    # --- New Highlighted AI Section ---
    st.markdown("---")
    with st.expander("🤖 PRO-TIP: Automate Your Data Entry with AI", expanded=True):
        st.markdown(
            """
            Tired of manually logging every transaction? You can automate most of this workflow!
            
            1.  **Use an AI Assistant:** Use an AI like ChatGPT or Gemini with the `AI_ASSISTANT_PROMPT.md` file found in this app's [GitHub repository](https://github.com/your-username/your-repo/blob/main/AI_ASSISTANT_PROMPT.md).
            2.  **Log on the Go:** Simply send your AI assistant text messages (e.g., *"₱500 groceries at SM"*) or upload receipt photos.
            3.  **Export to Google Sheets:** The prompt instructs the AI to log everything and export it as a CSV-formatted text.
            4.  **Connect to this App:** Just paste that text into your connected Google Sheet, and your dashboard will update automatically.
            
            This turns your AI assistant into a data entry clerk, and **Cash Cohort** into your personal analyst.
            """
        )

    st.markdown("---")
    st.info("Ready to start? Click on `Data Mapping` in the sidebar to load your data!")

if __name__ == "__main__":
    home_page()

