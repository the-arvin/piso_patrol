import streamlit as st
import pandas as pd
from utils import add_currency_selector, display_global_date_filter # Updated imports
import numpy as np
from datetime import datetime, timedelta # Added timedelta
from dateutil.relativedelta import relativedelta # Added for monthly projection

st.set_page_config(
    page_title="Piso Patrol - Stashes",
    page_icon="🏦",
    layout="wide"
)

def format_currency(amount, currency_symbol):
    """Formats a number as currency."""
    return f"{currency_symbol}{amount:,.2f}"

# --- NEW HELPER FUNCTION (MODIFIED) ---
def calculate_projection_string(all_time_df, goal_amount):
    """
    Calculates the estimated completion date for a stash goal
    based on the average *monthly* savings rate, projecting from the last contribution.
    """
    if all_time_df.empty:
        return "No contributions yet"
    
    total_saved_all_time = all_time_df['Amount'].sum()
    
    if total_saved_all_time >= goal_amount:
        return "Goal Met! 🎉"
        
    first_contribution_date = all_time_df['Date'].min().date()
    last_contribution_date = all_time_df['Date'].max().date()
    
    # Calculate number of months between first and last contribution
    num_months = (last_contribution_date.year - first_contribution_date.year) * 12 + (last_contribution_date.month - first_contribution_date.month) + 1
    
    if num_months <= 0:
        num_months = 1 # Avoid division by zero if all contributions in same month
        
    avg_monthly_rate = total_saved_all_time / num_months
    
    if avg_monthly_rate <= 0:
        return "Never (at this rate)"
        
    remaining_amount = goal_amount - total_saved_all_time
    # Use ceiling to round up to the next full month
    months_remaining = int(np.ceil(remaining_amount / avg_monthly_rate))
    
    try:
        # Project from the *last* contribution date, as requested
        estimated_date = last_contribution_date + relativedelta(months=months_remaining)
        return f"Est. {estimated_date.strftime('%b %d, %Y')}"
    except OverflowError:
        # Handle cases where the date is too far in the future
        return "Decades away"
# --- END NEW FUNCTION ---

def stashes_page():
    add_currency_selector()
    currency_symbol = st.session_state.get("currency_symbol", "$")
    
    st.title("🏦 Stashes & Savings Goals")
    st.markdown("Track your progress towards your savings goals. Define your stashes on the 'Data Mapping' page.")

    if "processed_data" not in st.session_state or st.session_state.processed_data.empty:
        st.warning("We don't have any data to analyze yet! 📂 Please head over to the 'Data Mapping' page to upload and process your financial data first.", icon="⚠️")
        st.page_link("pages/1_📑_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return
        
    if "stash_goals" not in st.session_state:
        # Initialize if it doesn't exist from Data Mapping
        st.session_state.stash_goals = {}
    if "stash_emojis" not in st.session_state:
        st.session_state.stash_emojis = {}
        
    # Main dataframe for this page
    all_df = st.session_state.processed_data.copy()
    all_df['Date'] = pd.to_datetime(all_df['Date'], errors='coerce')
    
    # --- NEW: Global Date Filter ---
    display_global_date_filter()
    if st.session_state.get("global_start_date") is None:
        st.info("Please select a date range from the sidebar to begin.", icon="🗓️")
        return
        
    start_date = st.session_state.global_start_date
    end_date = st.session_state.global_end_date
    
    # Filter by global date first
    date_mask = (all_df['Date'].dt.date >= start_date) & (all_df['Date'].dt.date <= end_date)
    df = all_df[date_mask] # df is now the *filtered* dataframe
    
    # --- Correct Stash Logic ---
    stash_subcategories = st.session_state.get('stash_goals', {}).keys()
    
    # Get ALL stash transactions from the *unfiltered* dataframe for projections
    stash_mask_all_time = (all_df['Type'] == 'Stash') | \
                         ((all_df['Type'] == 'Expense') & (all_df['Subcategory'].isin(stash_subcategories)))
    df_stashes_all_time = all_df[stash_mask_all_time].copy()
    
    # Get stash transactions from the *filtered* dataframe for period metrics
    stash_mask_filtered = (df['Type'] == 'Stash') | \
                         ((df['Type'] == 'Expense') & (df['Subcategory'].isin(stash_subcategories)))
    df_stashes_filtered = df[stash_mask_filtered].copy()

    # --- NEW: Standard Page Filters ---
    st.header("🗓️ Select Your Filters")
    st.markdown("Refine your analysis by filtering for specific accounts, categories, or subcategories.")

    with st.expander("Filters available here:", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            # Use df_stashes_filtered to get available filter options
            all_accounts = sorted(df_stashes_filtered['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts, key="stash_account_filter")

        with col2:
            all_categories = sorted(df_stashes_filtered['Category'].unique())
            selected_categories = st.multiselect("Filter by Category(s)", options=all_categories, default=all_categories, key="stash_cat_filter")

        with col3:
            if not selected_categories:
                available_subcategories = sorted(df_stashes_filtered['Subcategory'].unique())
            else:
                available_subcategories = sorted(df_stashes_filtered[df_stashes_filtered['Category'].isin(selected_categories)]['Subcategory'].unique())
            
            # Default to only the defined stash subcategories that are *also* in the filtered data
            default_subcategories = [s for s in available_subcategories if s in stash_subcategories]
            selected_subcategories = st.multiselect("Filter by Subcategory(s)", options=available_subcategories, default=default_subcategories, key="stash_subcat_filter")

    # --- NEW: Resurfaced Stash Definition Editor ---
    st.markdown("---")
    st.header("⚙️ Edit Your Stash Definitions")
    st.markdown("Manage your savings goals here. These changes will be saved globally across the app.")

    with st.expander("Edit Stash Goals & Emojis", expanded=False):
        # We must get ALL possible subcategories from the *entire* dataset
        all_expense_subcategories = sorted(all_df[
            (all_df['Type'] == 'Expense') | 
            (all_df['Type'] == 'Stash')
        ]['Subcategory'].unique())

        if not all_expense_subcategories:
            st.info("No expense or stash subcategories found in your data.")
        else:
            emoji_options = ["🏦", "💰", "✈️", "🚗", "🏠", "🎓", "🎁", "💻"]

            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown("**Select Stash Subcategories**")
                selected_stashes = st.multiselect(
                    "Select **subcategories** to track as stashes:",
                    options=all_expense_subcategories,
                    default=list(st.session_state.stash_goals.keys()),
                    key="stash_multiselect_editor"
                )

            temp_goals = {}
            temp_emojis = {}

            with col2:
                st.markdown("**Set Your Goals**")
                for stash in selected_stashes:
                    temp_goals[stash] = st.number_input(
                        f"Goal for {stash} ($)",
                        min_value=0.0,
                        value=st.session_state.stash_goals.get(stash, 0.0), # Recall
                        key=f"goal_editor_{stash}"
                    )
            
            with col3:
                st.markdown("**Assign Emojis**")
                for stash in selected_stashes:
                    temp_emojis[stash] = st.selectbox(
                        f"Emoji for {stash}",
                        options=emoji_options,
                        index=emoji_options.index(st.session_state.stash_emojis.get(stash, "🏦")), # Recall
                        key=f"emoji_editor_{stash}"
                    )
            
            if st.button("Save Stash Definitions", type="primary", key="save_stash_editor"):
                st.session_state.stash_goals = temp_goals
                st.session_state.stash_emojis = temp_emojis
                st.success("Stash goals and emojis have been saved!", icon="✅")
                st.rerun() 

    # --- End of new section ---

    # Apply all page filters
    account_mask = df_stashes_filtered['Account'].isin(selected_accounts)
    category_mask = df_stashes_filtered['Category'].isin(selected_categories)
    subcategory_mask = df_stashes_filtered['Subcategory'].isin(selected_subcategories)

    filtered_df = df_stashes_filtered[account_mask & category_mask & subcategory_mask] # This is now the *displayed* data

    if filtered_df.empty and not stash_subcategories:
        st.info("No stash goals defined. Please set your goals in the 'Edit Stash Definitions' section above or on the 'Data Mapping' page.", icon="🏦")
        return
    elif filtered_df.empty:
        st.info("No stash contributions found for the selected filters. Keep saving!", icon="💪")
        return

    # --- Stash Goal Progress (REWORKED LOGIC) ---
    st.markdown("---")
    st.header("🏆 Your Savings Progress")
    st.markdown("Here's a look at how your savings are stacking up against the goals you set.")

    # Get goals and emojis (they may have *just* been updated)
    stash_goals = st.session_state.get('stash_goals', {})
    stash_emojis = st.session_state.get('stash_emojis', {})

    # Calculate totals from the *filtered* data (for period metrics)
    grouped_stashes_filtered = filtered_df.groupby('Subcategory').agg(
        Contributed_in_Period=('Amount', 'sum'),
        Contributions_in_Period=('Amount', 'count'),
        Avg_Contribution_in_Period=('Amount', 'mean')
    ).to_dict('index')
    
    # Calculate totals from *all* data (for progress bar & projection)
    grouped_stashes_all_time = df_stashes_all_time.groupby('Subcategory').agg(
        Total_Saved_All_Time=('Amount', 'sum')
    ).to_dict('index')
    
    # We will display ALL defined stashes, regardless of filter
    stashes_to_show = sorted(list(stash_goals.keys()))
    
    if not stashes_to_show:
        st.info("No stash goals defined. Please set your goals in the 'Edit Stash Definitions' section above.", icon="🏦")
        st.stop()
        
    total_columns = min(len(stashes_to_show), 4) # Max 4 columns
    cols = st.columns(total_columns)
    col_index = 0

    for stash_name in stashes_to_show:
        goal_amount = stash_goals.get(stash_name, 0)
        emoji = stash_emojis.get(stash_name, "🏦")
        
        # Get ALL-TIME metrics
        all_time_data = grouped_stashes_all_time.get(stash_name)
        total_saved_all_time = all_time_data['Total_Saved_All_Time'] if all_time_data else 0
        
        # Get FILTERED metrics
        filtered_data = grouped_stashes_filtered.get(stash_name)
        contributed_in_period = filtered_data['Contributed_in_Period'] if filtered_data else 0
        contributions_in_period = filtered_data['Contributions_in_Period'] if filtered_data else 0
        avg_contribution_in_period = filtered_data['Avg_Contribution_in_Period'] if filtered_data else 0

        # Calculate attainment and progress
        attainment = (total_saved_all_time / goal_amount) * 100 if goal_amount > 0 else 0
        progress_bar_value = min(attainment / 100, 1.0)
        
        # Calculate projection
        projection = calculate_projection_string(
            df_stashes_all_time[df_stashes_all_time['Subcategory'] == stash_name],
            goal_amount
        )
        
        with cols[col_index % total_columns]:
            with st.container(border=True):
                st.markdown(f"<h5>{emoji} {stash_name}</h5>", unsafe_allow_html=True)
                
                # Goal and Progress (based on ALL-TIME data)
                st.markdown(f"**Goal:** {format_currency(goal_amount, currency_symbol)}")
                st.progress(progress_bar_value, text=f"{attainment:.1f}% Complete")
                st.markdown(f"**Total Saved:** {format_currency(total_saved_all_time, currency_symbol)}")
                st.markdown(f"**Est. Goal Date:** {projection}")
                
                # Metrics (based on FILTERED data)
                st.markdown("---")
                st.markdown(f"**Contributed (in period):** {format_currency(contributed_in_period, currency_symbol)}")
                st.markdown(f"**Contributions (in period):** {contributions_in_period}")
                st.markdown(f"**Avg. Contribution (in period):** {format_currency(avg_contribution_in_period, currency_symbol)}")
        
        col_index += 1
        
    # --- NEW: Full Transaction Table ---
    st.markdown("---")
    st.header("🧾 All Stash Transactions")
    st.markdown("Here is a complete list of all your stash contributions for the selected period.")

    # --- Add local filters for the transaction table ---
    st.markdown("##### Filter this table:")
    
    # Use the FILTEERED df for these options
    available_cats_table = ['All'] + sorted(filtered_df['Category'].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        table_filter_cat = st.selectbox("Filter by Category", options=available_cats_table, key="table_cat_filter_stash")

    with col2:
        if table_filter_cat == 'All':
            available_subcats_table = ['All'] + sorted(filtered_df['Subcategory'].unique())
        else:
            available_subcats_table = ['All'] + sorted(filtered_df[filtered_df['Category'] == table_filter_cat]['Subcategory'].unique())
        
        table_filter_subcat = st.selectbox("Filter by Subcategory", options=available_subcats_table, key="table_subcat_filter_stash")

    # Create a copy to display
    table_df = filtered_df.copy() # Start with the page-filtered data

    # Apply local filters
    if table_filter_cat != 'All':
        table_df = table_df[table_df['Category'] == table_filter_cat]
    
    if table_filter_subcat != 'All':
        table_df = table_df[table_df['Subcategory'] == table_filter_subcat]
    
    # Columns to show
    columns_to_show = ['Date', 'Amount', 'Category', 'Subcategory', 'Account']
    if 'Subcategory' not in table_df.columns:
        table_df['Subcategory'] = table_df['Category'] # Fallback
        
    st.dataframe(table_df[columns_to_show],
                 use_container_width=True, 
                 hide_index=True,
                 column_config={
                     "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                     "Amount": st.column_config.NumberColumn("Amount", format=f"{currency_symbol}%.2f"),
                     "Category": st.column_config.TextColumn("Category"),
                     "Subcategory": st.column_config.TextColumn("Subcategory"),
                     "Account": st.column_config.TextColumn("Account")
                 })

if __name__ == "__main__":
    stashes_page()

