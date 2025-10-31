import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def add_currency_selector():
    """
    Adds a currency selector to the Streamlit sidebar.
    The selected currency symbol is stored in st.session_state.currency_symbol.
    """
    st.sidebar.header("Currency 🪙")
    currencies = {
        "USD ($)": "$",
        "EUR (€)": "€",
        "GBP (£)": "£",
        "JPY (¥)": "¥",
        "INR (₹)": "₹",
        "PHP (₱)": "₱",
    }
    selected_currency_label = st.sidebar.selectbox(
        "Select your currency",
        options=currencies.keys(),
        index=5 # Default to PHP
    )
    st.session_state.currency_symbol = currencies[selected_currency_label]

def display_filters(df):
    """
    Displays the main filters in an expander on the main page.
    Returns: start_date, end_date, selected_accounts, selected_categories
    """
    with st.expander("Filters available here:", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            # --- Date Filtering ---
            today = datetime.now().date()
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()

            date_options = [
                "All Time", "This Week", "This Month", "Last 30 Days", "This Quarter",
                "Year to Date", "Custom"
            ]
            selected_option = st.selectbox("Choose a date range", date_options)

            if selected_option == "This Week":
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif selected_option == "This Month":
                start_date = today.replace(day=1)
                end_date = today
            elif selected_option == "Last 30 Days":
                start_date = today - timedelta(days=30)
                end_date = today
            elif selected_option == "This Quarter":
                quarter_start_month = (today.month - 1) // 3 * 3 + 1
                start_date = today.replace(month=quarter_start_month, day=1)
                end_date = today
            elif selected_option == "Year to Date":
                start_date = today.replace(month=1, day=1)
                end_date = today
            elif selected_option == "All Time":
                start_date = min_date
                end_date = max_date
            else: # Custom
                start_date, end_date = st.date_input(
                    "Select your custom date range",
                    (min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
        with col2:
            # --- Account Filtering ---
            all_accounts = sorted(df['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts)
        with col3:
            # --- Category Filtering ---
            all_categories = sorted(df['Category'].unique())
            selected_categories = st.multiselect("Filter by Category(s)", options=all_categories, default=all_categories)
    
    return start_date, end_date, selected_accounts, selected_categories

def display_sidebar_stash_filters(df):
    """
    Displays the filters for the Stash page in the sidebar.
    Returns: start_date, end_date, selected_accounts
    """
    # with st.sidebar.expander("Filters 🗓️", expanded=True):
        # --- Date Filtering ---
    today = datetime.now().date()
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()

    date_options = [
        "All Time", "This Week", "This Month", "Last 30 Days", "This Quarter",
        "Year to Date", "Custom"
    ]
    selected_option = st.selectbox("Choose a date range", date_options, key="stash_date_filter")

    if selected_option == "This Week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif selected_option == "This Month":
        start_date = today.replace(day=1)
        end_date = today
    elif selected_option == "Last 30 Days":
        start_date = today - timedelta(days=30)
        end_date = today
    elif selected_option == "This Quarter":
        quarter_start_month = (today.month - 1) // 3 * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        end_date = today
    elif selected_option == "Year to Date":
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif selected_option == "All Time":
        start_date = min_date
        end_date = max_date
    else: # Custom
        start_date, end_date = st.date_input(
            "Select your custom date range",
            (min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="stash_date_input"
        )
    
    # --- Account Filtering ---
    all_accounts = sorted(df['Account'].unique())
    selected_accounts = st.multiselect(
        "Filter by Account(s)", 
        options=all_accounts, 
        default=all_accounts,
        key="stash_account_filter"
    )
    
    return start_date, end_date, selected_accounts

