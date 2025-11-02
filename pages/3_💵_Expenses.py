import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils import add_currency_selector, display_global_date_filter
from dateutil.relativedelta import relativedelta
import calendar
import numpy as np

st.set_page_config(
    page_title="Piso Patrol - Expenses",
    page_icon="💸",
    layout="wide"
)

def format_currency(amount, currency_symbol):
    """Formats a number as currency."""
    return f"{currency_symbol}{amount:,.2f}"

def calculate_ytd_average(df, group_col, item_name, selected_month_start):
    """
    Calculates the YTD monthly average for a specific category/subcategory,
    excluding the selected month.
    """
    # FIX: Compare date objects (.dt.date) to date objects (selected_month_start)
    ytd_df = df[
        (df['Date'].dt.date < selected_month_start) &
        (df['Date'].dt.date >= selected_month_start.replace(month=1, day=1)) &
        (df[group_col] == item_name)
    ]
    
    if ytd_df.empty:
        return 0.0

    # Find number of months with spending
    months_with_spending = ytd_df['Date'].dt.to_period('M').nunique()
    if months_with_spending == 0:
        return 0.0
        
    ytd_total = ytd_df['Amount'].sum()
    return ytd_total / months_with_spending

def expenses_page():
    """
    This page provides a detailed analysis of the user's expenses.
    """
    add_currency_selector()
    currency_symbol = st.session_state.get("currency_symbol", "$")
    
    st.title("💸 Expense Deep Dive")
    st.markdown("Let's take a closer look at where your money is going. Use the tools on this page to analyze your spending habits.")

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

    # --- Stash/Expense Logic ---
    stash_subcategories = st.session_state.get('stash_goals', {}).keys()
    
    # Correct Expense Mask: Type is 'Expense' AND Subcategory is NOT in the stash list
    expense_mask = (df['Type'] == 'Expense') & (~df['Subcategory'].isin(stash_subcategories))
    
    # Apply the mask to get only true expenses
    df_expenses = df[expense_mask].copy()

    # --- Data Filtering (Account, Category, Subcategory) ---
    st.header("🗓️ Select Your Filters")
    st.markdown("Refine your analysis by filtering for specific accounts, categories, or subcategories.")

    with st.expander("Filters available here:", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            all_accounts = sorted(df_expenses['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts)

        with col2:
            all_categories = sorted(df_expenses['Category'].unique())
            selected_categories = st.multiselect("Filter by Category(s)", options=all_categories, default=all_categories)

        with col3:
            if not selected_categories:
                available_subcategories = sorted(df_expenses['Subcategory'].unique())
            else:
                available_subcategories = sorted(df_expenses[df_expenses['Category'].isin(selected_categories)]['Subcategory'].unique())
            
            selected_subcategories = st.multiselect("Filter by Subcategory(s)", options=available_subcategories, default=available_subcategories)

    # Apply all filters
    account_mask = df_expenses['Account'].isin(selected_accounts)
    category_mask = df_expenses['Category'].isin(selected_categories)
    subcategory_mask = df_expenses['Subcategory'].isin(selected_subcategories)

    filtered_df = df_expenses[account_mask & category_mask & subcategory_mask]

    if filtered_df.empty:
        st.info("No expense transactions found for the selected filters. Looks like you're saving money!", icon="🎉")
        return

    # --- Expense-Specific KPIs ---
    st.markdown("---")
    st.header("📈 Expense Metrics")
    st.markdown("Here are the key numbers for your spending in this period.")

    total_expenses = filtered_df['Amount'].sum()
    num_transactions = len(filtered_df)
    largest_expense = filtered_df['Amount'].max()
    num_days = (end_date - start_date).days + 1
    avg_daily_spend = total_expenses / num_days if num_days > 0 else 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Expenses", format_currency(total_expenses, currency_symbol),border=True)
    kpi2.metric("Number of Transactions", f"{num_transactions}",border=True)
    kpi3.metric("Average Daily Spend", format_currency(avg_daily_spend, currency_symbol),border=True)
    kpi4.metric("Largest Single Expense", format_currency(largest_expense, currency_symbol),border=True)

    # --- Automated Insights ---
    st.markdown("---")
    st.header("🤖 Automated Insights")
    st.markdown("Get a quick analysis of your spending habits. How does this month compare to the last, or to your yearly average?")

    # Get all unique months from the filtered data for the selector
    available_months = sorted(filtered_df['Date'].dt.to_period('M').unique(), reverse=True)
    if not available_months:
        st.info("Not enough data to generate insights.")
        # We 'return' here because the rest of the page depends on this check
        st.stop() # Use st.stop() to halt execution gracefully if no months

    # Format months for display (e.g., "October 2025")
    month_display_options = [month.strftime('%B %Y') for month in available_months]
    selected_month_str = st.selectbox("Select a month to analyze", options=month_display_options)
    
    if not selected_month_str:
        st.stop() # Exit if no month is selected

    selected_month_period = available_months[month_display_options.index(selected_month_str)]
    selected_month_start = selected_month_period.to_timestamp().date()
    
    # Get previous month
    prev_month_period = selected_month_period - 1
    prev_month_start = prev_month_period.to_timestamp().date()
    
    # Filter data for the two months
    this_month_df = filtered_df[filtered_df['Date'].dt.to_period('M') == selected_month_period]
    # Use df_expenses (which is only filtered by global date) for last_month_df and YTD calcs
    last_month_df = df_expenses[df_expenses['Date'].dt.to_period('M') == prev_month_period] 

    # --- Insight Tabs ---
    insight_tab1, insight_tab2 = st.tabs(["By Category", "By Subcategory"])

    with insight_tab1:
        st.subheader(f"Category Insights for {selected_month_str}")
        
        this_month_grouped = this_month_df.groupby('Category')['Amount'].sum()
        last_month_grouped = last_month_df.groupby('Category')['Amount'].sum()
        
        all_insight_categories = sorted(list(set(this_month_grouped.index) | set(last_month_grouped.index)))
        
        if not all_insight_categories:
            st.info("No category spending data for this month.")
        else:
            insights_data = []
            for category in all_insight_categories:
                this_month_spend = this_month_grouped.get(category, 0)
                last_month_spend = last_month_grouped.get(category, 0)
                
                # YTD Average Calculation
                ytd_avg_spend = calculate_ytd_average(df_expenses, 'Category', category, selected_month_start)
                
                insights_data.append({
                    "Category": category,
                    "This Month": this_month_spend,
                    "Last Month": last_month_spend,
                    "vs. Last Month (%)": (this_month_spend - last_month_spend) / last_month_spend * 100 if last_month_spend > 0 else np.inf,
                    "vs. YTD Avg (%)": (this_month_spend - ytd_avg_spend) / ytd_avg_spend * 100 if ytd_avg_spend > 0 else np.inf
                })

            insights_df = pd.DataFrame(insights_data).sort_values(by=["vs. Last Month (%)","vs. YTD Avg (%)"])
            
            st.dataframe(insights_df, 
                         column_config={
                             "This Month": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "Last Month": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "vs. Last Month (%)": st.column_config.NumberColumn(format="%.1f%%"),
                             "vs. YTD Avg (%)": st.column_config.NumberColumn(format="%.1f%%")
                         },
                         use_container_width=True)

    with insight_tab2:
        st.subheader(f"Subcategory Insights for {selected_month_str}")
        
        this_month_grouped_sub = this_month_df.groupby('Subcategory')['Amount'].sum()
        last_month_grouped_sub = last_month_df.groupby('Subcategory')['Amount'].sum()
        
        all_insight_subcategories = sorted(list(set(this_month_grouped_sub.index) | set(last_month_grouped_sub.index)))
        
        if not all_insight_subcategories:
            st.info("No subcategory spending data for this month.")
        else:
            insights_data_sub = []
            for subcategory in all_insight_subcategories:
                this_month_spend = this_month_grouped_sub.get(subcategory, 0)
                last_month_spend = last_month_grouped_sub.get(subcategory, 0)
                
                # YTD Average Calculation
                ytd_avg_spend = calculate_ytd_average(df_expenses, 'Subcategory', subcategory, selected_month_start)
                
                insights_data_sub.append({
                    "Subcategory": subcategory,
                    "This Month": this_month_spend,
                    "Last Month": last_month_spend,
                    "vs. Last Month (%)": (this_month_spend - last_month_spend) / last_month_spend * 100 if last_month_spend > 0 else np.inf,
                    "vs. YTD Avg (%)": (this_month_spend - ytd_avg_spend) / ytd_avg_spend * 100 if ytd_avg_spend > 0 else np.inf
                })

            insights_df_sub = pd.DataFrame(insights_data_sub).sort_values(by=["vs. Last Month (%)","vs. YTD Avg (%)"])
            
            st.dataframe(insights_df_sub, 
                         column_config={
                             "Subcategory": st.column_config.TextColumn("Subcategory"),
                             "This Month": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "Last Month": st.column_config.NumberColumn(format=f"{currency_symbol}%.2f"),
                             "vs. Last Month (%)": st.column_config.NumberColumn(format="%.1f%%"),
                             "vs. YTD Avg (%)": st.column_config.NumberColumn(format="%.1f%%")
                         },
                         use_container_width=True)

    # --- Visualizations ---
    st.markdown("---")
    st.header("🎨 Visual Analysis")

    # --- Spending Trends Over Time ---
    st.subheader("Spending Trends Over Time")
    st.markdown("Analyze your spending patterns from different perspectives. Do you spend more on weekends? Or at the beginning of the month?")
    
    # Add toggle for Category vs Subcategory
    trend_granularity = st.radio(
        "Analyze trends by:",
        ("Category", "Subcategory"),
        horizontal=True,
        key="trend_granularity"
    )

    # Create a consistent color map for the selected granularity
    if trend_granularity == "Category":
        all_groups_in_df = sorted(filtered_df['Category'].unique())
        group_col = 'Category'
    else:
        all_groups_in_df = sorted(filtered_df['Subcategory'].unique())
        group_col = 'Subcategory'
        
    color_sequence = px.colors.qualitative.Plotly + px.colors.qualitative.G10 + px.colors.qualitative.Alphabet
    color_map = {group: color_sequence[i % len(color_sequence)] for i, group in enumerate(all_groups_in_df)}

    tab1, tab2, tab3, tab4 = st.tabs(["Daily Trend", "By Day of Week", "By Week of Month", "By Month"])

    with tab1:
        st.markdown("##### Daily Spending")
        daily_spend = filtered_df.groupby([filtered_df['Date'].dt.date, group_col])['Amount'].sum().reset_index().rename(columns={'Date': 'Date_str'})
        if not daily_spend.empty:
            fig_daily_spend = px.bar(daily_spend, x='Date_str', y='Amount', color=group_col, 
                                     labels={'Amount': 'Total Spend', 'Date_str': 'Date'},
                                     color_discrete_map=color_map,
                                     title=f"Daily Spending by {trend_granularity}")
            fig_daily_spend.update_layout(xaxis_title='Date', yaxis_title=f'Amount ({currency_symbol})', height=400, barmode='stack')
            st.plotly_chart(fig_daily_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    with tab2:
        st.markdown("##### Spending by Day of the Week")
        weekday_df = filtered_df.copy()
        weekday_df['weekday'] = weekday_df['Date'].dt.day_name()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_df['weekday'] = pd.Categorical(weekday_df['weekday'], categories=weekday_order, ordered=True)
        spend_by_weekday = weekday_df.groupby(['weekday', group_col])['Amount'].sum().reset_index()
        if not spend_by_weekday.empty:
            fig_weekday_spend = px.bar(spend_by_weekday, x='weekday', y='Amount', color=group_col, 
                                       labels={'Amount': 'Total Spend', 'weekday': 'Day of the Week'},
                                       color_discrete_map=color_map,
                                       title=f"Spending by Day of Week (by {trend_granularity})")
            fig_weekday_spend.update_layout(xaxis_title='Day of the Week', yaxis_title=f'Amount ({currency_symbol})', height=400, barmode='stack')
            st.plotly_chart(fig_weekday_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    with tab3:
        st.markdown("##### Spending by Week of the Month")
        week_of_month_df = filtered_df.copy()
        week_of_month_df['week_of_month'] = (week_of_month_df['Date'].dt.day - 1) // 7 + 1
        spend_by_week = week_of_month_df.groupby(['week_of_month', group_col])['Amount'].sum().reset_index()
        if not spend_by_week.empty:
            fig_week_spend = px.bar(spend_by_week, x='week_of_month', y='Amount', color=group_col, 
                                    labels={'Amount': 'Total Spend', 'week_of_month': 'Week of the Month'},
                                    color_discrete_map=color_map,
                                    title=f"Spending by Week of Month (by {trend_granularity})")
            fig_week_spend.update_layout(xaxis_title='Week of the Month', yaxis_title=f'Amount ({currency_symbol})', height=400, barmode='stack')
            st.plotly_chart(fig_week_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    with tab4:
        st.markdown("##### Spending by Month")
        month_df = filtered_df.copy()
        spend_by_month = month_df.groupby([pd.Grouper(key='Date', freq='MS'), group_col])['Amount'].sum().reset_index()
        
        # --- FIX: Sort by date to ensure chronological order ---
        spend_by_month = spend_by_month.sort_values(by='Date')
        
        spend_by_month['month_str'] = spend_by_month['Date'].dt.strftime('%B %Y') 
        
        # --- NEW ROBUST FIX ---
        # Create an explicit list of the chronological month strings
        chronological_month_list = spend_by_month['month_str'].unique().tolist()
        
        if not spend_by_month.empty and spend_by_month['Amount'].sum() > 0:
            fig_month_spend = px.bar(spend_by_month, x='month_str', y='Amount', color=group_col, 
                                     labels={'Amount': 'Total Spend', 'month_str': 'Month'},
                                     color_discrete_map=color_map,
                                     title=f"Spending by Month (by {trend_granularity})")
            
            # --- Tell Plotly to use the EXPLICIT order we just created ---
            fig_month_spend.update_xaxes(
                type='category',
                categoryorder='array',
                categoryarray=chronological_month_list
            )
            
            fig_month_spend.update_layout(xaxis_title='Month', yaxis_title=f'Amount ({currency_symbol})', height=400, xaxis={'tickangle': -45}, barmode='stack')
            st.plotly_chart(fig_month_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    # --- Category Deep Dive (Treemap) ---
    st.markdown("---")
    st.subheader("Category Deep Dive")
    st.markdown("Wondering where the bulk of your money goes? This hierarchical treemap makes it crystal clear. Click on a category (like 'Food & Dining') to see the subcategories inside. 🌳")
    
    # Clean data for treemap: remove NaN paths
    treemap_df = filtered_df.copy()
    treemap_df['Category'] = treemap_df['Category'].fillna('Uncategorized')
    treemap_df['Subcategory'] = treemap_df['Subcategory'].fillna('Uncategorized')
    
    # Ensure there are no 0 values which can cause issues
    if treemap_df['Amount'].sum() > 0:
        fig_treemap = px.treemap(
            treemap_df,
            path=[px.Constant("All Expenses"), 'Category', 'Subcategory'], # Hierarchical path
            values='Amount',
            color='Amount',
            color_continuous_scale='Reds',
            hover_data={'Amount': f':.2f'}
        )
        fig_treemap.update_layout(
            title_text='Expense Breakdown by Category & Subcategory',
            margin=dict(t=50, l=25, r=25, b=25)
        )
        fig_treemap.update_traces(
            hovertemplate='<b>%{label}</b><br>Total Spend: ' + currency_symbol + '%{value:,.2f}<br>Percentage of Parent: %{percentParent:.1%}'
        )
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info("No positive spending data to display in the treemap.")


    # --- Spending Habits & Bubble Chart ---
    st.markdown("---")
    st.subheader("Your Spending Habits at a Glance")
    st.markdown("This summary shows your top categories based on how much you spent, how often you spent, and how recently you spent.")

    # Add toggle for Category vs Subcategory
    habit_granularity = st.selectbox(
        "Analyze habits by:",
        ("Subcategory", "Category"),
        key="habit_granularity"
    )
    
    # Aggregate data based on selected granularity
    grouped_habits = filtered_df.groupby(habit_granularity).agg(
        Total_Spend=('Amount', 'sum'),
        Frequency=('Amount', 'count'),
        Avg_Spend=('Amount', 'mean'),
        Most_Recent=('Date', 'max')
    ).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"##### 📊 Bubble Chart by {habit_granularity}")
        if not grouped_habits.empty:
            fig_bubble = px.scatter(
                grouped_habits,
                x="Frequency",
                y="Avg_Spend",
                size="Total_Spend",
                color=habit_granularity,
                hover_name=habit_granularity,
                size_max=60,
                log_x=True,
                log_y=True,
                title=f"Spending Habits by {habit_granularity}"
            )
            fig_bubble.update_layout(
                xaxis_title="Frequency (Number of Transactions)",
                yaxis_title=f"Average Spend ({currency_symbol})",
                height=500
            )
            fig_bubble.update_traces(
                hovertemplate=(
                    f'<b>%{{hovertext}}</b><br>' +
                    'Frequency: %{x}<br>' +
                    f'Avg. Spend: {currency_symbol}%{{y:,.2f}}<br>' +
                    f'Total Spend: {currency_symbol}%{{marker.size:,.2f}}'
                )
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("No data for bubble chart.")

    with col2:
        st.markdown(f"##### 📋 Detailed Breakdown by {habit_granularity}")
        st.dataframe(
            grouped_habits.sort_values("Total_Spend", ascending=False),
            column_config={
                habit_granularity: st.column_config.TextColumn("Item"),
                "Total_Spend": st.column_config.NumberColumn("Total Spend", format=f"{currency_symbol}%.2f"),
                "Frequency": st.column_config.NumberColumn("Transactions"),
                "Avg_Spend": st.column_config.NumberColumn("Avg. Spend", format=f"{currency_symbol}%.2f"),
                "Most_Recent": st.column_config.DateColumn("Last Purchase")
            },
            use_container_width=True,
            hide_index=True
        )

    # --- Full Transaction Table ---
    st.markdown("---")
    
    
    # --- NEW: Add local filters for the transaction table ---
    # Get available categories/subcategories from the *already filtered* dataframe
    available_cats = ['All'] + sorted(filtered_df['Category'].unique())
    available_subcats = ['All'] + sorted(filtered_df['Subcategory'].unique())

    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        st.header("🧾 All Expense Transactions")
        st.markdown("Here is a complete list of all your expenses for the selected period. You can search and sort the table to find specific transactions.")
    with col2:
        #st.markdown("##### Filter this table:")
        table_filter_cat = st.selectbox("Categories", options=available_cats, key="table_cat_filter")
    with col3:
        #st.markdown("##### ")
        table_filter_subcat = st.selectbox("Subcategories", options=available_subcats, key="table_subcat_filter")

    # Create a copy to display
    table_df = filtered_df.copy()

    # Apply local filters
    if table_filter_cat != 'All':
        table_df = table_df[table_df['Category'] == table_filter_cat]
    
    if table_filter_subcat != 'All':
        table_df = table_df[table_df['Subcategory'] == table_filter_subcat]
    # --- END NEW FILTERS ---

    # Ensure Subcategory column is present
    if 'Subcategory' not in table_df.columns:
        table_df['Subcategory'] = table_df['Category'] # Fallback
        
    st.dataframe(table_df[['Date', 'Amount', 'Category', 'Subcategory', 'Account', 'Type']], 
                 use_container_width=True, 
                 hide_index=True,
                 column_config={
                     "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                     "Amount": st.column_config.NumberColumn("Amount", format=f"{currency_symbol}%.2f")
                 })

if __name__ == "__main__":
    expenses_page()

