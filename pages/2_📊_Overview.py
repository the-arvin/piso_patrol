import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px # Added missing import
from datetime import datetime, timedelta
from utils import add_currency_selector # Import the new function

st.set_page_config(
    page_title="Financial Overview",
    page_icon="📊",
    layout="wide"
)

def overview_page():
    """
    This page provides a high-level overview of the user's finances.
    """
    add_currency_selector() # Add the currency selector to the sidebar
    currency_symbol = st.session_state.get("currency_symbol", "$")

    st.title("📊 Financial Overview")
    st.markdown("Your financial command center. Get a bird's-eye view of your income, expenses, and savings for any period.")

    if "processed_data" not in st.session_state or st.session_state.processed_data.empty:
        st.warning("We don't have any data to analyze yet! 📂 Please head over to the 'Data Mapping' page to upload and process your financial data first.", icon="⚠️")
        st.page_link("pages/2_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return

    df = st.session_state.processed_data
    
    # Ensure Date column is datetime before filtering
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        st.session_state.processed_data = df # Save back to session state


    # --- Data Filtering ---
    
    st.header("🗓️ Select Your Filters")
    st.markdown("Slice and dice your data just the way you like it! 🕵️‍♀️ Use the filters below to focus on specific accounts, categories, or time periods.")
    with st.expander("Filters available here:",expanded=False):

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
                if min_date > max_date:
                    start_date, end_date = st.date_input("Select your custom date range", (max_date, max_date), min_value=max_date, max_value=max_date)
                else:
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


    # Apply all filters
    date_mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    account_mask = df['Account'].isin(selected_accounts)
    category_mask = df['Category'].isin(selected_categories)

    filtered_df = df[date_mask & account_mask & category_mask]


    if filtered_df.empty:
        st.info("No transactions found for the selected filters. Try adjusting your selections!", icon="🧐")
        return
        
    # --- Data Segmentation (Income, Expense, Stash) ---
    stash_categories = list(st.session_state.get('stash_goals', {}).keys())
    
    # A stash transaction is either Type 'Stash' OR (Type 'Expense' AND Category is in stash_categories)
    stash_mask = (filtered_df['Type'] == 'Stash') | \
                   ((filtered_df['Type'] == 'Expense') & (filtered_df['Category'].isin(stash_categories)))
    
    # Separate dataframes for easier calculations
    # Stashes are *removed* from expenses
    expense_df = filtered_df[(filtered_df['Type'] == 'Expense') & (~stash_mask)]
    income_df = filtered_df[filtered_df['Type'] == 'Income']
    stash_df = filtered_df[stash_mask]

    # --- High-Level KPIs ---
    st.markdown("---")
    st.header("📈 Key Metrics")
    st.markdown("Here's the big picture! 🖼️ These are your headline numbers for the selected period.")

    total_income = income_df['Amount'].sum()
    total_expenses = expense_df['Amount'].sum()
    total_stashed = stash_df['Amount'].sum()
    total_savings = total_income - total_expenses - total_stashed

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 Total Income", f"{currency_symbol}{total_income:,.2f}",border=True)
    kpi2.metric("💸 Total Expenses", f"{currency_symbol}{total_expenses:,.2f}",border=True)
    kpi3.metric("🏦 Total Stashed", f"{currency_symbol}{total_stashed:,.2f}",border=True)
    kpi4.metric(
        "📊 Net Savings" if total_savings >= 0 else "📉 Net Deficit",
        f"{currency_symbol}{total_savings:,.2f}",
        delta=f"{total_savings:,.2f}", # Added delta argument
        delta_color=("inverse" if total_savings < 0 else "normal"), border=True
    )

    # --- Time Series Analysis ---
    st.header("📊 Cumulative Financials Over Time")
    st.markdown("How are you trending? 📉 This chart shows your financial journey over time, tracking how your savings grow (or shrink!).")
    
    # Resample data for a clean cumulative chart
    income_daily = income_df.set_index('Date').resample('D')['Amount'].sum().reset_index().rename(columns={'Amount': 'Income'})
    expense_daily = expense_df.set_index('Date').resample('D')['Amount'].sum().reset_index().rename(columns={'Amount': 'Expense'})
    stash_daily = stash_df.set_index('Date').resample('D')['Amount'].sum().reset_index().rename(columns={'Amount': 'Stash'})

    # Merge all daily data
    merged_df = pd.merge(income_daily, expense_daily, on='Date', how='outer')
    merged_df = pd.merge(merged_df, stash_daily, on='Date', how='outer').fillna(0).sort_values('Date')

    # Calculate cumulative sums
    merged_df['Cumulative Income'] = merged_df['Income'].cumsum()
    merged_df['Cumulative Expense'] = merged_df['Expense'].cumsum()
    merged_df['Cumulative Stash'] = merged_df['Stash'].cumsum()
    merged_df['Cumulative Net Savings'] = merged_df['Cumulative Income'] - merged_df['Cumulative Expense'] - merged_df['Cumulative Stash']

    # Create the Plotly figure for the time series
    fig_time_series = go.Figure()

    # Add traces for Income, Expense, Stash, and Net Savings
    fig_time_series.add_trace(go.Scatter(
        x=merged_df['Date'], y=merged_df['Cumulative Income'],
        mode='lines', name='Cumulative Income', line=dict(color='green'),
        fill='tozeroy',
        fillcolor='rgba(0,128,0,0.2)' # Green with transparency
    ))
    fig_time_series.add_trace(go.Scatter(
        x=merged_df['Date'], y=merged_df['Cumulative Expense'],
        mode='lines', name='Cumulative Expense', line=dict(color='red'),
        fill='tozeroy',
        fillcolor='rgba(255,0,0,0.2)' # Red with transparency
    ))
    fig_time_series.add_trace(go.Scatter(
        x=merged_df['Date'], y=merged_df['Cumulative Stash'],
        mode='lines', name='Cumulative Stash', line=dict(color='blue'),
        fill='tozeroy',
        fillcolor='rgba(0,0,255,0.2)' # Blue with transparency
    ))
    fig_time_series.add_trace(go.Scatter(
        x=merged_df['Date'], y=merged_df['Cumulative Net Savings'],
        mode='lines', name='Net Savings', line=dict(color='gold', dash='dash', width=3)
    ))

    fig_time_series.update_layout(
        title='Cumulative Financials Over Selected Period',
        xaxis_title='Date',
        yaxis_title=f'Amount ({currency_symbol})',
        legend_title='Metric',
        height=450
    )
    st.plotly_chart(fig_time_series, use_container_width=True)


    # --- Visualizations ---
    st.markdown("---")
    st.header("🎨 Visual Analysis")
    st.markdown("Let's get visual! 🧐 These charts help you compare your totals and see exactly where your money is going.")

    # Bar Chart - Full Width
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=['Income'], y=[total_income], name='Income', marker_color='green'
    ))
    fig_bar.add_trace(go.Bar(
        x=['Expenses'], y=[total_expenses], name='Expenses', marker_color='red'
    ))
    fig_bar.add_trace(go.Bar(
        x=['Stashes'], y=[total_stashed], name='Stashes', marker_color='blue'
    ))
    fig_bar.update_layout(
        title_text='Income vs. Expenses vs. Stashes',
        yaxis_title=f'Amount ({currency_symbol})',
        barmode='group',
        height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("### Category Breakdowns")
    st.markdown("A proportional look at where your money came from, where it went, and where you've saved it.")

    # --- Pie Charts with Proportional Sizing ---
    # Create column spec, handling potential division by zero
    total_all = total_income + total_expenses + total_stashed
    if total_all == 0:
        # If all are zero, just use equal columns
        col_spec = [1, 1, 1]
    else:
        # Set a minimum width (e.g., 0.1) to ensure visibility even for small amounts
        col_spec = [
            max(0.1, total_income / total_all),
            max(0.1, total_expenses / total_all),
            max(0.1, total_stashed / total_all)
        ]

    pie1, pie2, pie3 = st.columns(3)#col_spec

    with pie1:
        if total_income > 0:
            income_category_spend = income_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            fig_income_donut = go.Figure(data=[go.Pie(
                labels=income_category_spend.index,
                values=income_category_spend.values,
                hole=.4,
                pull=[0.05] * len(income_category_spend.index),
                marker_colors=px.colors.sequential.Greens_r,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Amount: %{value:,.2f}<br>Percent: %{percent}'
            )])
            fig_income_donut.update_layout(title_text='Income Breakdown', height=400, showlegend=False)
            st.plotly_chart(fig_income_donut, use_container_width=True)
        else:
            st.info("No Income to display.")

    with pie2:
        if total_expenses > 0:
            expense_category_spend = expense_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            fig_expense_donut = go.Figure(data=[go.Pie(
                labels=expense_category_spend.index,
                values=expense_category_spend.values,
                hole=.4,
                pull=[0.05] * len(expense_category_spend.index),
                marker_colors=px.colors.sequential.Reds_r,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Amount: %{value:,.2f}<br>Percent: %{percent}'
            )])
            fig_expense_donut.update_layout(title_text='Expense Breakdown', height=400, showlegend=False)
            st.plotly_chart(fig_expense_donut, use_container_width=True)
        else:
            st.info("No Expenses to display.")

    with pie3:
        if total_stashed > 0:
            stash_category_spend = stash_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            fig_stash_donut = go.Figure(data=[go.Pie(
                labels=stash_category_spend.index,
                values=stash_category_spend.values,
                hole=.4,
                pull=[0.05] * len(stash_category_spend.index),
                marker_colors=px.colors.sequential.Blues_r,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Amount: %{value:,.2f}<br>Percent: %{percent}'
            )])
            fig_stash_donut.update_layout(title_text='Stash Breakdown', height=400, showlegend=False)
            st.plotly_chart(fig_stash_donut, use_container_width=True)
        else:
            st.info("No Stash contributions to display.")

    # --- Detailed Transactions ---
    st.markdown("---")
    st.header("🧾 Transaction Details")
    st.markdown("Want to see the fine print? 📝 Here are all the individual transactions for the period, split by type.")

    trans1, trans2, trans3 = st.columns(3)

    with trans1:
        with st.expander(f"💰 Incomes ({len(income_df)})"):
            st.dataframe(income_df.sort_values('Date', ascending=False), hide_index=True, use_container_width=True)

    with trans2:
        with st.expander(f"💸 Expenses ({len(expense_df)})"):
            st.dataframe(expense_df.sort_values('Date', ascending=False), hide_index=True, use_container_width=True)

    with trans3:
        with st.expander(f"🏦 Stash Contributions ({len(stash_df)})"):
            st.dataframe(stash_df.sort_values('Date', ascending=False), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    overview_page()

