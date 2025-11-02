import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils import add_currency_selector, display_global_date_filter
import calendar
import numpy as np

st.set_page_config(
    page_title="Piso Patrol - Income",
    page_icon="💰",
    layout="wide"
)

def format_currency(amount, currency_symbol):
    """Formats a number as currency."""
    return f"{currency_symbol}{amount:,.2f}"

def calculate_ytd_comparison(df, group_col, item_name, selected_month_start):
    """
    Calculates the YTD comparison for a specific category/subcategory
    against the first month of the year.
    """
    first_month_of_year = selected_month_start.replace(month=1)
    
    # --- FIX: Convert the datetime.date object to a Period object for comparison ---
    first_month_period = pd.Period(first_month_of_year, freq='M')
    
    # Get data for the first month of the year
    first_month_df = df[
        (df['Date'].dt.to_period('M') == first_month_period) &
        (df[group_col] == item_name)
    ]
    
    first_month_spend = first_month_df['Amount'].sum()
    return first_month_spend

# --- NEW FUNCTION ---
def calculate_ytd_average_income(df, group_col, item_name, selected_month_start):
    """
    Calculates the YTD monthly average for a specific category/subcategory,
    excluding the selected month, only for months with income.
    """
    # Filter for YTD, *excluding* the selected month
    ytd_df = df[
        (df['Date'].dt.date < selected_month_start) &
        (df['Date'].dt.date >= selected_month_start.replace(month=1, day=1)) &
        (df[group_col] == item_name)
    ]
    
    if ytd_df.empty:
        return 0.0

    # Find number of unique months with income for this item
    months_with_income = ytd_df['Date'].dt.to_period('M').nunique()
    if months_with_income == 0:
        return 0.0
        
    ytd_total = ytd_df['Amount'].sum()
    return ytd_total / months_with_income
# --- END NEW FUNCTION ---

def income_page():
    """
    This page provides a detailed analysis of the user's income.
    """
    add_currency_selector()
    currency_symbol = st.session_state.get("currency_symbol", "$")
    
    st.title("💰 Income Analysis")
    st.markdown("Track your earnings, understand your income streams, and see how they change over time.")

    if "processed_data" not in st.session_state or st.session_state.processed_data.empty:
        st.warning("We don't have any data to analyze yet! 📂 Please head over to the 'Data Mapping' page to upload and process your financial data first.", icon="⚠️")
        st.page_link("pages/1_📑_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return

    df = st.session_state.processed_data.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # --- Global Date Filter ---
    display_global_date_filter()
    if st.session_state.get("global_start_date") is None:
        st.info("Please select a date range from the sidebar to begin.", icon="🗓️")
        return
        
    start_date = st.session_state.global_start_date
    end_date = st.session_state.global_end_date
    
    # Filter by global date first
    date_mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    df = df[date_mask]

    # --- Income Logic ---
    income_mask = df['Type'] == 'Income'
    df_income = df[income_mask].copy()

    # --- Data Filtering (Account, Category, Subcategory) ---
    st.header("🗓️ Select Your Filters")
    st.markdown("Refine your analysis by filtering for specific accounts, categories, or subcategories.")

    with st.expander("Filters available here:", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            all_accounts = sorted(df_income['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts)

        with col2:
            all_categories = sorted(df_income['Category'].unique())
            selected_categories = st.multiselect("Filter by Category(s)", options=all_categories, default=all_categories)

        with col3:
            if not selected_categories:
                available_subcategories = sorted(df_income['Subcategory'].unique())
            else:
                available_subcategories = sorted(df_income[df_income['Category'].isin(selected_categories)]['Subcategory'].unique())
            
            selected_subcategories = st.multiselect("Filter by Subcategory(s)", options=available_subcategories, default=available_subcategories)

    # Apply all filters
    account_mask = df_income['Account'].isin(selected_accounts)
    category_mask = df_income['Category'].isin(selected_categories)
    subcategory_mask = df_income['Subcategory'].isin(selected_subcategories)

    filtered_df = df_income[account_mask & category_mask & subcategory_mask]

    if filtered_df.empty:
        st.info("No income transactions found for the selected filters.", icon="🧐")
        return

    # --- Income-Specific KPIs ---
    st.markdown("---")
    st.header("📈 Income Metrics")
    st.markdown("Here are the key numbers for your income in this period.")

    total_income = filtered_df['Amount'].sum()
    num_transactions = len(filtered_df)
    avg_income_event = total_income / num_transactions if num_transactions > 0 else 0
    largest_income = filtered_df['Amount'].max()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        with st.container(border=True):
            st.metric("Total Income", format_currency(total_income, currency_symbol))
    with kpi2:
        with st.container(border=True):
            st.metric("Income Events", f"{num_transactions}")
    with kpi3:
        with st.container(border=True):
            st.metric("Avg. Income Event", format_currency(avg_income_event, currency_symbol))
    with kpi4:
        with st.container(border=True):
            st.metric("Largest Income Event", format_currency(largest_income, currency_symbol))

    # --- Automated Insights (YTD) ---
    st.markdown("---")
    st.header("🤖 Automated Insights (YTD)")
    st.markdown("See how your income streams are changing compared to the start of the year.")

    # Get all unique months from the filtered data for the selector
    # Use df_income (only filtered by global date) to get all possible months
    available_months = sorted(df_income['Date'].dt.to_period('M').unique(), reverse=True)
    if not available_months:
        st.info("Not enough data to generate insights.")
        st.stop()

    month_display_options = [month.strftime('%B %Y') for month in available_months]
    selected_month_str = st.selectbox("Select a month to analyze", options=month_display_options, key="income_insight_month")
    
    if not selected_month_str:
        st.stop()

    selected_month_period = available_months[month_display_options.index(selected_month_str)]
    selected_month_start = selected_month_period.to_timestamp().date()
    
    # Use filtered_df for "This Month"
    this_month_df = filtered_df[filtered_df['Date'].dt.to_period('M') == selected_month_period]
    
    insight_tab1, insight_tab2 = st.tabs(["By Category", "By Subcategory"])

    with insight_tab1:
        st.subheader(f"Category YTD Insights for {selected_month_str}")
        group_col = 'Category'
        
        this_month_grouped_cat = this_month_df.groupby(group_col)['Amount'].sum()
        # Use df_income (global date filter only) for historical data
        all_insight_items_cat = sorted(df_income[df_income['Category'].isin(this_month_grouped_cat.index)]['Category'].unique())
        
        if not all_insight_items_cat:
            st.info(f"No income data for this month at the {group_col} level.")
        else:
            insights_data_cat = []
            for item in all_insight_items_cat:
                this_month_income = this_month_grouped_cat.get(item, 0)
                # Use df_income for historical calculations
                first_month_income = calculate_ytd_comparison(df_income, group_col, item, selected_month_start)
                ytd_avg_income = calculate_ytd_average_income(df_income, group_col, item, selected_month_start) # NEW
                
                insights_data_cat.append({
                    group_col: item,
                    "This Month's Income": this_month_income,
                    "First Month's Income": first_month_income,
                    "YTD Avg. Income": ytd_avg_income, # NEW
                    "vs. First Month (%)": (this_month_income - first_month_income) / first_month_income * 100 if first_month_income > 0 else np.inf,
                    "vs. YTD Avg (%)": (this_month_income - ytd_avg_income) / ytd_avg_income * 100 if ytd_avg_income > 0 else np.inf # NEW
                })

            insights_df_cat = pd.DataFrame(insights_data_cat).sort_values(by="This Month's Income", ascending=False)
            
            st.dataframe(insights_df_cat, 
                         column_config={
                             group_col: st.column_config.TextColumn(group_col),
                             "This Month's Income": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "First Month's Income": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "YTD Avg. Income": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"), # NEW
                             "vs. First Month (%)": st.column_config.NumberColumn(format="%.1f%%"),
                             "vs. YTD Avg (%)": st.column_config.NumberColumn(format="%.1f%%") # NEW
                         },
                         use_container_width=True)

    with insight_tab2:
        st.subheader(f"Subcategory YTD Insights for {selected_month_str}")
        group_col = 'Subcategory'

        this_month_grouped_sub = this_month_df.groupby(group_col)['Amount'].sum()
        # Use df_income (global date filter only) for historical data
        all_insight_items_sub = sorted(df_income[df_income['Subcategory'].isin(this_month_grouped_sub.index)]['Subcategory'].unique())
        
        if not all_insight_items_sub:
            st.info(f"No income data for this month at the {group_col} level.")
        else:
            insights_data_sub = []
            for item in all_insight_items_sub:
                this_month_income = this_month_grouped_sub.get(item, 0)
                # Use df_income for historical calculations
                first_month_income = calculate_ytd_comparison(df_income, group_col, item, selected_month_start)
                ytd_avg_income = calculate_ytd_average_income(df_income, group_col, item, selected_month_start) # NEW

                insights_data_sub.append({
                    group_col: item,
                    "This Month's Income": this_month_income,
                    "First Month's Income": first_month_income,
                    "YTD Avg. Income": ytd_avg_income, # NEW
                    "vs. First Month (%)": (this_month_income - first_month_income) / first_month_income * 100 if first_month_income > 0 else np.inf,
                    "vs. YTD Avg (%)": (this_month_income - ytd_avg_income) / ytd_avg_income * 100 if ytd_avg_income > 0 else np.inf # NEW
                })

            insights_df_sub = pd.DataFrame(insights_data_sub).sort_values(by="This Month's Income", ascending=False)
            
            st.dataframe(insights_df_sub, 
                         column_config={
                             group_col: st.column_config.TextColumn(group_col),
                             "This Month's Income": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "First Month's Income": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "YTD Avg. Income": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"), # NEW
                             "vs. First Month (%)": st.column_config.NumberColumn(format="%.1f%%"),
                             "vs. YTD Avg (%)": st.column_config.NumberColumn(format="%.1f%%") # NEW
                         },
                         use_container_width=True)

    # --- Visualizations ---
    st.markdown("---")
    st.header("🎨 Visual Analysis")

    col1, col2 = st.columns(2)
    
    with col1:
        # --- NEW: Upgraded to Sunburst Chart ---
        st.subheader("Income Sources Breakdown")
        st.markdown("See where your income comes from, from broad categories to specific subcategories.")
        
        sunburst_df = filtered_df.copy()
        sunburst_df['Category'] = sunburst_df['Category'].fillna('Uncategorized')
        sunburst_df['Subcategory'] = sunburst_df['Subcategory'].fillna('Uncategorized')
        
        if sunburst_df['Amount'].sum() > 0:
            fig_sunburst = px.sunburst(
                sunburst_df,
                path=['Subcategory'],#[px.Constant("All Income"), 'Category', 'Subcategory'],
                values='Amount',
                color='Amount',
                color_continuous_scale='Greens',
            )
            fig_sunburst.update_layout(
                title_text='Income Breakdown by Category & Subcategory',
                margin=dict(t=50, l=25, r=25, b=25)
            )
            fig_sunburst.update_traces(
                hovertemplate='<b>%{label}</b><br>Total Income: ' + currency_symbol + '%{value:,.2f}<br>Percentage of Parent: %{percentParent:.1%}',
                textinfo="label+percent root"
            )
            st.plotly_chart(fig_sunburst, use_container_width=True)
        else:
            st.info("No income data to display in the sunburst chart.")

    with col2:
        # --- NEW: Trend chart with granularity toggle ---
        st.subheader("Monthly Income Trend")
        group_col_trend = "Subcategory"

        month_df = filtered_df.copy()
        spend_by_month = month_df.groupby([pd.Grouper(key='Date', freq='MS'), group_col_trend])['Amount'].sum().reset_index()
        
        spend_by_month = spend_by_month.sort_values(by='Date')
        spend_by_month['month_str'] = spend_by_month['Date'].dt.strftime('%B %Y') 
        
        chronological_month_list = spend_by_month['month_str'].unique().tolist()
        
        if not spend_by_month.empty and spend_by_month['Amount'].sum() > 0:
            # Create color map
            all_groups_in_df = sorted(filtered_df[group_col_trend].unique())
            color_sequence = px.colors.qualitative.Plotly + px.colors.qualitative.G10
            color_map = {group: color_sequence[i % len(color_sequence)] for i, group in enumerate(all_groups_in_df)}

            fig_month_spend = px.bar(spend_by_month, x='month_str', y='Amount', color=group_col_trend, 
                                     labels={'Amount': 'Total Income', 'month_str': 'Month'},
                                     color_discrete_map=color_map,
                                     title=f"Monthly Income Trend by {group_col_trend}",
                                     text='Amount' # Add text labels
                                     )
            
            fig_month_spend.update_xaxes(
                type='category',
                categoryorder='array',
                categoryarray=chronological_month_list
            )
            
            # Format text labels
            fig_month_spend.update_traces(
                texttemplate=f'{currency_symbol}%{{y:,.0f}}', 
                textposition='inside'
            )
            
            fig_month_spend.update_layout(
                xaxis_title='Month', 
                yaxis_title=f'Amount ({currency_symbol})', 
                height=400, 
                xaxis={'tickangle': -45}, 
                barmode='stack',
                uniformtext_minsize=8, 
                uniformtext_mode='hide'
            )
            st.plotly_chart(fig_month_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    # --- Full Transaction Table ---
    st.markdown("---")
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        st.header("🧾 All Income Transactions")
        st.markdown("Here is a complete list of all your income for the selected period.")
    
    # --- NEW: Add local filters AND granularity for the transaction table ---
    
    available_cats_table = ['All'] + sorted(filtered_df['Category'].unique())
    
   
    with col2:
        table_filter_cat = st.selectbox("Filter by Category", options=available_cats_table, key="table_cat_filter_income")
    
    with col3:
        if table_filter_cat == 'All':
                    available_subcats_table = ['All'] + sorted(filtered_df['Subcategory'].unique())
        else:
            available_subcats_table = ['All'] + sorted(filtered_df[filtered_df['Category'] == table_filter_cat]['Subcategory'].unique())
        
        table_filter_subcat = st.selectbox("Filter by Subcategory", options=available_subcats_table, key="table_subcat_filter_income")
               
    
    table_df = filtered_df.copy()

    if table_filter_cat != 'All':
        table_df = table_df[table_df['Category'] == table_filter_cat]
    
    if table_filter_subcat != 'All':
        table_df = table_df[table_df['Subcategory'] == table_filter_subcat]
    
    columns_to_show = ['Date', 'Amount','Category', 'Subcategory', 'Account']

    if 'Subcategory' not in table_df.columns:
        table_df['Subcategory'] = table_df['Category']
        
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
    income_page()

