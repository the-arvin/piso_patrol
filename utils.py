import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def add_currency_selector():
    st.sidebar.markdown("---")
    st.sidebar.header("💱 Currency Selector")
    
    currency_options = {
        "USD ($)": "$",
        "PHP (₱)": "₱",
        "EUR (€)": "€",
        "GBP (£)": "£",
        "JPY (¥)": "¥",
    }
    
    selected_currency_label = st.sidebar.selectbox(
        "Choose your currency",
        options=list(currency_options.keys()),
        key="selected_currency"
    )
    
    st.session_state.currency_symbol = currency_options[selected_currency_label]

def display_global_date_filter():
    """
    Displays a global date filter in the sidebar if processed_data is available.
    Saves the selected start and end dates to session_state.
    """
    if "processed_data" in st.session_state and not st.session_state.processed_data.empty:
        df = st.session_state.processed_data
        st.sidebar.markdown("---")
        st.sidebar.header("🗓️ Global Date Filter")
        
        try:
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()

            if min_date > max_date:
                st.sidebar.error("Warning: Your data's minimum date is after the maximum date. Please check your data.")
                # Set a sensible default to avoid crashing
                min_date = max_date
        
        except Exception as e:
            st.sidebar.error(f"Error processing dates: {e}. Defaulting to today.")
            min_date = datetime.now().date()
            max_date = datetime.now().date()
            
        today = datetime.now().date()

        date_options = [
            "All Time", "This Week", "This Month", "Last 30 Days", "This Quarter",
            "Year to Date", "Custom"
        ]
        
        # Use session_state to keep the selection persistent
        selected_option = st.sidebar.selectbox(
            "Choose a date range", 
            date_options, 
            key="global_date_option",
            index=date_options.index(st.session_state.get("global_date_option", "All Time"))
        )

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
            # Use persistent dates if available, else default to min/max
            default_start = st.session_state.get("global_start_date", min_date)
            default_end = st.session_state.get("global_end_date", max_date)
            
            if min_date > max_date:
                 start_date, end_date = st.sidebar.date_input("Select your custom date range", (max_date, max_date), min_value=max_date, max_value=max_date, key="global_custom_date")
            else:
                # Ensure defaults are within the min/max bounds
                if default_start < min_date: default_start = min_date
                if default_end > max_date: default_end = max_date
                
                start_date, end_date = st.sidebar.date_input(
                    "Select your custom date range",
                    (default_start, default_end),
                    min_value=min_date,
                    max_value=max_date,
                    key="global_custom_date"
                )
        
        # Save to session state
        st.session_state.global_start_date = start_date
        st.session_state.global_end_date = end_date
        
        return # start_date, end_date
    
    # Return defaults if no data
    st.session_state.global_start_date = None
    st.session_state.global_end_date = None
    return #  None, None
