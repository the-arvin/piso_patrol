import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px # Still needed for colors
from datetime import datetime, timedelta
from utils import add_currency_selector ,display_global_date_filter
import numpy as np # Ensure numpy is imported

st.set_page_config(
    page_title="Piso Patrol - Overview",
    page_icon="📊",
    layout="wide"
)

def overview_page():
    """
    This page provides a high-level overview of the user's finances.
    """
    add_currency_selector() # Add the currency selector to the sidebar
    currency_symbol = st.session_state.get("currency_symbol", "$")
    display_global_date_filter() # Display the global date filter if applicable
    
    st.title("📊 Financial Overview")
    st.markdown("Your financial command center. Get a bird's-eye view of your income, expenses, and savings for any period.")

    if "processed_data" not in st.session_state or st.session_state.processed_data.empty:
        st.warning("We don't have any data to analyze yet! 📂 Please head over to the 'Data Mapping' page to upload and process your financial data first.", icon="⚠️")
        st.page_link("pages/1_📑_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return
    
    df = st.session_state.processed_data
    # Ensure Date column is in datetime format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    if st.session_state.get("global_start_date") is not None and st.session_state.get("global_end_date") is not None:
        start_date = st.session_state.get("global_start_date")
        end_date = st.session_state.get("global_end_date")
        date_mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
        df = df[date_mask]
        
    # --- Data Filtering ---
    st.header("🗓️ Select Your Filters")
    st.markdown("Slice and dice your data just the way you like it! 🕵️‍♀️ Use the filters below to focus on specific accounts, categories, or subcategories.")
    with st.expander("Filters available here:",expanded=False):

        col2, col3 = st.columns(2)
        
        # --- New Cascading Filters ---
        with col2:
            # --- Account Filtering ---
            all_accounts = sorted(df['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts)
            
            # --- Category Filtering ---
            all_categories = sorted(df['Category'].unique())
            selected_categories = st.multiselect("Filter by Category(s)", options=all_categories, default=all_categories)

        with col3:
            # --- Subcategory Filtering (Dynamic) ---
            if not selected_categories:
                available_subcategories = sorted(df['Subcategory'].unique())
            else:
                available_subcategories = sorted(df[df['Category'].isin(selected_categories)]['Subcategory'].unique())
            
            selected_subcategories = st.multiselect("Filter by Subcategory(s)", options=available_subcategories, default=available_subcategories)


    # Apply all filters
    date_mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    account_mask = df['Account'].isin(selected_accounts)
    category_mask = df['Category'].isin(selected_categories)
    subcategory_mask = df['Subcategory'].isin(selected_subcategories) # New mask

    filtered_df = df[date_mask & account_mask & category_mask & subcategory_mask] # Updated filter application


    if filtered_df.empty:
        st.info("No transactions found for the selected filters. Try adjusting your selections!", icon="🧐")
        return

    # --- Stash Calculation Update ---
    # Get stash subcategories from session state
    stash_subcategories = st.session_state.get('stash_goals', {}).keys()
    
    # New Stash Mask:
    # A transaction is a "Stash" if:
    # 1. Its Type is explicitly 'Stash'
    # 2. Its Type is 'Expense' AND its Subcategory is in the defined stash list
    stash_mask = (filtered_df['Type'] == 'Stash') | \
                 ((filtered_df['Type'] == 'Expense') & (filtered_df['Subcategory'].isin(stash_subcategories)))
    
    # New Expense Mask:
    # An "Expense" is:
    # 1. Its Type is 'Expense'
    # 2. AND it is NOT a stash (as defined above)
    expense_mask = (filtered_df['Type'] == 'Expense') & (~stash_mask)
    
    income_mask = filtered_df['Type'] == 'Income'

    # --- High-Level KPIs ---
    st.markdown("---")
    st.header("📈 Key Metrics")
    st.markdown("Here's the big picture! 🖼️ These are your headline numbers for the selected period.")

    total_income = filtered_df[income_mask]['Amount'].sum()
    total_expenses = filtered_df[expense_mask]['Amount'].sum() # Use new expense mask
    total_stashed = filtered_df[stash_mask]['Amount'].sum() # Use new stash mask
    # --- CALCULATION UPDATED AS REQUESTED ---
    # This now represents Total Savings = (Income - NonStash_Expenses) + Stash_Contributions
    net_savings = total_income + total_stashed - total_expenses 

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        with st.container(border=True):
            st.metric("💰 Total Income", f"{currency_symbol}{total_income:,.2f}")
    with kpi2:
        with st.container(border=True):
            st.metric("💸 Total Expenses", f"{currency_symbol}{total_expenses:,.2f}")
    with kpi3:
        with st.container(border=True):
            st.metric("🏦 Total Stashed", f"{currency_symbol}{total_stashed:,.2f}")
    with kpi4:
        with st.container(border=True):
            st.metric(
                "Total Savings", # Renamed label to reflect new calculation
                f"{currency_symbol}{net_savings:,.2f}",
                delta=f"{net_savings:,.2f}",
                delta_color=("inverse" if net_savings < 0 else "normal")
            )

    # --- Time Series Analysis ---
    st.header("📊 Cumulative Financials Over Time")
    st.markdown("How are you trending? 📉 This chart shows your financial journey over time, tracking how your savings grow (or shrink!).")
    
    # Make a copy to avoid changing the original filtered_df and sort by date
    time_series_df = filtered_df.copy().sort_values('Date')
    
    # Get stash subcategories again for this dataframe
    stash_subcategories_ts = st.session_state.get('stash_goals', {}).keys()
    
    # Create separate income, expense, and stash columns for cumulative calculation
    def get_type(row):
        if row['Type'] == 'Income':
            return 'Income'
        if row['Type'] == 'Stash' or (row['Type'] == 'Expense' and row['Subcategory'] in stash_subcategories_ts):
            return 'Stash'
        if row['Type'] == 'Expense':
            return 'Expense'
        return 'Other'

    time_series_df['Tx_Type'] = time_series_df.apply(get_type, axis=1)
    
    time_series_df['Income'] = time_series_df.apply(lambda row: row['Amount'] if row['Tx_Type'] == 'Income' else 0, axis=1)
    time_series_df['Expense'] = time_series_df.apply(lambda row: row['Amount'] if row['Tx_Type'] == 'Expense' else 0, axis=1)
    time_series_df['Stash'] = time_series_df.apply(lambda row: row['Amount'] if row['Tx_Type'] == 'Stash' else 0, axis=1) # New

    # Calculate cumulative sums
    time_series_df['Cumulative Income'] = time_series_df['Income'].cumsum()
    time_series_df['Cumulative Expense'] = time_series_df['Expense'].cumsum()
    time_series_df['Cumulative Stash'] = time_series_df['Stash'].cumsum() # New
    # --- CALCULATION UPDATED AS REQUESTED ---
    time_series_df['Cumulative Total Savings'] = time_series_df['Cumulative Income'] + time_series_df['Cumulative Stash'] - time_series_df['Cumulative Expense']

    # Create the Plotly figure for the time series
    fig_time_series = go.Figure()

    # Add traces for Income, Expense, Stash, and Net Savings
    fig_time_series.add_trace(go.Scatter(
        x=time_series_df['Date'], y=time_series_df['Cumulative Income'],
        mode='lines', name='Cumulative Income', line=dict(color='green'),
        fill='tozeroy',
        fillcolor='rgba(0,128,0,0.2)' # Green with transparency
    ))
    fig_time_series.add_trace(go.Scatter(
        x=time_series_df['Date'], y=time_series_df['Cumulative Expense'],
        mode='lines', name='Cumulative Expense', line=dict(color='red'),
        fill='tozeroy',
        fillcolor='rgba(255,0,0,0.2)' # Red with transparency
    ))
    fig_time_series.add_trace(go.Scatter(
        x=time_series_df['Date'], y=time_series_df['Cumulative Stash'], # New
        mode='lines', name='Cumulative Stash', line=dict(color='orange'),
        fill='tozeroy',
        fillcolor='rgba(255,165,0,0.2)' # Orange with transparency
    ))
    fig_time_series.add_trace(go.Scatter(
        x=time_series_df['Date'], y=time_series_df['Cumulative Total Savings'], # Updated variable
        mode='lines', name='Total Savings', line=dict(color='blue', dash='dash') # Updated label
    ))

    fig_time_series.update_layout(
        title='Cumulative Financials Over Selected Period',
        xaxis_title='Date',
        yaxis_title=f'Amount ({currency_symbol})',
        legend_title='Metric',
        height=450
    )
    st.plotly_chart(fig_time_series, use_container_width=True) # Use container width


    # --- Visualizations ---
    st.markdown("---")
    st.header("🎨 Visual Analysis")
    st.markdown("Let's get visual! 🧐 These charts help you compare your income to your expenses and see exactly where your money is going.")

    # Bar chart for Income vs Expense vs Stash
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=['Income'], y=[total_income], name='Income', marker_color='green'
    ))
    fig_bar.add_trace(go.Bar(
        x=['Expenses'], y=[total_expenses], name='Expenses', marker_color='red'
    ))
    fig_bar.add_trace(go.Bar(
        x=['Stashes'], y=[total_stashed], name='Stashes', marker_color='orange' # New
    ))
    fig_bar.update_layout(
        title_text='Income vs. Expenses vs. Stashes',
        yaxis_title=f'Amount ({currency_symbol})',
        barmode='group',
        height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True) # Use container width

    # --- Reverted to Pie Charts, Grouped by Subcategory ---
    st.markdown("### 📊 Breakdown by Subcategory")
    
    # Calculate column widths
    total_all = total_income + total_expenses + total_stashed
    if total_all == 0: # Avoid division by zero
        income_col_width = 1
        expense_col_width = 1
        stash_col_width = 1
    else:
        income_col_width = max(1, int(total_income / total_all * 10))
        expense_col_width = max(1, int(total_expenses / total_all * 10))
        stash_col_width = max(1, int(total_stashed / total_all * 10))

    vis1, vis2, vis3 = st.columns(3)#(income_col_width, expense_col_width, stash_col_width)

    with vis1:
        st.subheader("💰 Income Sources")
        income_df = filtered_df[income_mask].copy()
        if income_df.empty:
            st.info("No income data to display.")
        else:
            # Group by Subcategory
            subcategory_income = income_df.groupby('Subcategory')['Amount'].sum().sort_values(ascending=False)
            fig_pie_income = go.Figure(data=[go.Pie(
                labels=subcategory_income.index,
                values=subcategory_income.values,
                hole=.4,
                pull=[0.05] * len(subcategory_income.index),
                textinfo="label+percent" # Add labels
            )])
            fig_pie_income.update_layout(
                title_text='Income Breakdown by Subcategory',
                height=400,
                margin=dict(t=50, l=0, r=0, b=0)
            )
            st.plotly_chart(fig_pie_income, use_container_width=True)


    with vis2:
        st.subheader("💸 Expense Breakdown")
        expense_df = filtered_df[expense_mask].copy()
        if expense_df.empty:
            st.info("No expense data to display.")
        else:
            # Group by Subcategory
            subcategory_expense = expense_df.groupby('Subcategory')['Amount'].sum().sort_values(ascending=False)
            fig_pie_expense = go.Figure(data=[go.Pie(
                labels=subcategory_expense.index,
                values=subcategory_expense.values,
                hole=.4,
                pull=[0.05] * len(subcategory_expense.index),
                textinfo="label+percent" # Add labels
            )])
            fig_pie_expense.update_layout(
                title_text='Expense Breakdown by Subcategory',
                height=400,
                margin=dict(t=50, l=0, r=0, b=0)
            )
            st.plotly_chart(fig_pie_expense, use_container_width=True)

    with vis3:
        st.subheader("🏦 Stash Breakdown")
        stash_df = filtered_df[stash_mask].copy()
        if stash_df.empty:
            st.info("No stash data to display.")
        else:
            # Group by Subcategory
            subcategory_stash = stash_df.groupby('Subcategory')['Amount'].sum().sort_values(ascending=False)
            fig_pie_stash = go.Figure(data=[go.Pie(
                labels=subcategory_stash.index,
                values=subcategory_stash.values,
                hole=.4,
                pull=[0.05] * len(subcategory_stash.index),
                textinfo="label+percent" # Add labels
            )])
            fig_pie_stash.update_layout(
                title_text='Stash Breakdown by Subcategory',
                height=400,
                margin=dict(t=50, l=0, r=0, b=0)
            )
            st.plotly_chart(fig_pie_stash, use_container_width=True)

    # --- Detailed Transactions ---
    st.markdown("---")
    st.header("🧾 Transaction Details")
    st.markdown("Want to see the fine print? 📝 Here are all the individual transactions for the period, split by type.")

    trans1, trans2, trans3 = st.columns(3) # Updated to 3 columns

    with trans1:
        with st.expander("💸 Expenses in Period"):
            expense_details = filtered_df[expense_mask].sort_values('Date', ascending=False)
            st.dataframe(expense_details, use_container_width=True, hide_index=True)

    with trans2:
        with st.expander("💰 Incomes in Period"):
            income_details = filtered_df[income_mask].sort_values('Date', ascending=False)
            st.dataframe(income_details, use_container_width=True, hide_index=True)
            
    with trans3:
        with st.expander("🏦 Stashes in Period"):
            stash_details = filtered_df[stash_mask].sort_values('Date', ascending=False)
            st.dataframe(stash_details, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    overview_page()

