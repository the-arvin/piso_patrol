import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils import add_currency_selector
import calendar # Needed for month calculations

st.set_page_config(
    page_title="Expense Analysis",
    page_icon="💸",
    layout="wide"
)

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
        st.page_link("pages/2_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return

    df = st.session_state.processed_data
    # Ensure Date column is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # --- Data Filtering (Consistent with Overview Page) ---
    st.header("🗓️ Select Your Filters")
    st.markdown("Just like the Overview page, you can filter your expenses by date, account, or category to focus your analysis.")

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
            
            # Default to "This Month"
            selected_option = st.selectbox("Choose a date range", date_options, index=0)

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
                date_range = st.date_input(
                    "Select your custom date range",
                    (min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                if len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    # Handle case where user hasn't selected a range yet
                    start_date, end_date = min_date, max_date
        
        with col2:
        # --- Account Filtering ---
            all_accounts = sorted(df['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts)

        with col3:
            # --- Category Filtering ---
            all_categories = sorted(df['Category'].unique())
            selected_categories = st.multiselect("Filter by Category(s)", options=all_categories, default=all_categories)

    # Apply all filters for the main page
    date_mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    account_mask = df['Account'].isin(selected_accounts)
    category_mask = df['Category'].isin(selected_categories)
    expense_mask = df['Type'] == 'Expense'

    # This is the filtered data for the main charts
    filtered_df = df[date_mask & account_mask & category_mask & expense_mask]

    if filtered_df.empty:
        st.info("No expense transactions found for the selected filters. Looks like you're saving money!", icon="🎉")
        # We don't return here, so insights can still run on the whole dataset if the user wants
        pass # Continue to insights

    # --- Expense-Specific KPIs (based on main filter) ---
    st.markdown("---")
    st.header("📈 Expense Metrics")
    st.markdown("Here are the key numbers for your spending *in the period selected above*.")

    if filtered_df.empty:
        st.info("No expense transactions found for the selected filters.", icon="🧐")
    else:
        total_expenses = filtered_df['Amount'].sum()
        num_transactions = len(filtered_df)
        largest_expense = filtered_df['Amount'].max()
        num_days = (end_date - start_date).days + 1
        avg_daily_spend = total_expenses / num_days if num_days > 0 else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Expenses", f"{currency_symbol}{total_expenses:,.2f}")
        kpi2.metric("Number of Transactions", f"{num_transactions}")
        kpi3.metric("Average Daily Spend", f"{currency_symbol}{avg_daily_spend:,.2f}")
        kpi4.metric("Largest Single Expense", f"{currency_symbol}{largest_expense:,.2f}")

    # --- Automated Insights Section ---
    st.markdown("---")
    cl1,cl2 = st.columns([5,1])
    with cl1:
        st.header("💡 Automated Insights")
        st.markdown("Analyze month-over-month trends for any month. *Note: Insights are based on the Account and Category filters set above.*")

        mom_insights_increases = []
        mom_insights_decreases = []
        pacing_insights = []
        today = datetime.now().date()
        
        # Create month selector for insights
        expense_df_for_insights = df[expense_mask & account_mask & category_mask] # Use main filters
        if expense_df_for_insights.empty:
            st.info("No expense data available to generate insights.")
        else:
            # Create a list of available months in "Month YYYY" format
            available_months = expense_df_for_insights['Date'].dt.to_period('M').unique()
            available_months = sorted(available_months, reverse=True)
            month_options = [month.strftime('%B %Y') for month in available_months]
            
            # Default to current month if available, otherwise most recent
            current_month_str = today.strftime('%B %Y')
            if current_month_str in month_options:
                default_index = month_options.index(current_month_str)
            else:
                default_index = 0 # Default to the most recent month
    
        with cl2:
            selected_month_str = st.selectbox(
                "Select a month to analyze:",
                month_options,
                index=default_index
            )
    
        
        top_increases = pd.DataFrame()
        top_decreases = pd.DataFrame()
        
        # --- Run Insight Calculations ---
        try:
            # 1. Month-over-Month (MoM) Insights
            selected_month_dt = datetime.strptime(selected_month_str, '%B %Y').date()
            insight_start_date = selected_month_dt.replace(day=1)
            # Find the last day of the selected month
            _, last_day = calendar.monthrange(insight_start_date.year, insight_start_date.month)
            insight_end_date = insight_start_date.replace(day=last_day)

            # Get last month's data
            last_month_end = insight_start_date - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            # Filter for the selected month
            current_month_mask = (expense_df_for_insights['Date'].dt.date >= insight_start_date) & (expense_df_for_insights['Date'].dt.date <= insight_end_date)
            current_month_df = expense_df_for_insights[current_month_mask]
            
            # Filter for the previous month
            last_month_mask = (expense_df_for_insights['Date'].dt.date >= last_month_start) & (expense_df_for_insights['Date'].dt.date <= last_month_end)
            last_month_df = expense_df_for_insights[last_month_mask]
            
            current_month_spend = current_month_df.groupby('Category')['Amount'].sum()
            last_month_spend = last_month_df.groupby('Category')['Amount'].sum()

            comparison = pd.DataFrame({'Current': current_month_spend, 'Previous': last_month_spend}).fillna(0)
            comparison = comparison[(comparison['Previous'] > 0) | (comparison['Current'] > 0)] # Compare if spending in either
            
            if not comparison.empty:
                comparison['Change (%)'] = ((comparison['Current'] - comparison['Previous']) / comparison['Previous']) * 100
                comparison = comparison.sort_values(by='Change (%)', ascending=False)
                
                # Replace inf with 100% for cases where Previous was 0
                comparison.replace([float('inf'), float('-inf')], 100.0, inplace=True) 

                top_increases = comparison[comparison['Change (%)'] > 10].head(3)
                top_decreases = comparison[comparison['Change (%)'] < -10].sort_values(by='Change (%)', ascending=True).head(3)

            
            if not top_increases.empty:
                mom_insights_increases.append("**Top Increases:**")
                for idx, row in top_increases.iterrows():
                    if row['Previous'] == 0:
                        mom_insights_increases.append(f"🔺 **{idx}**: {currency_symbol}{row['Current']:,.0f} (New spending this month)")
                    else:
                        mom_insights_increases.append(f"🔺 **{idx}**: {currency_symbol}{row['Current']:,.0f} (Up {row['Change (%)']:.0f}% from {currency_symbol}{row['Previous']:,.0f})")

            if not top_decreases.empty:
                mom_insights_decreases.append("**Top Decreases:**")
                for idx, row in top_decreases.iterrows():
                    mom_insights_decreases.append(f"✅ **{idx}**: {currency_symbol}{row['Current']:,.0f} (Down {abs(row['Change (%)']):.0f}% from {currency_symbol}{row['Previous']:,.0f})")
            
            # 2. Pacing vs. Average Insights
            # Only run if the selected month is the *actual current* month and it's not over
            if selected_month_str == current_month_str and today <= insight_end_date and today.day < 28:
                percent_of_month_passed = today.day / pd.Timestamp(today).days_in_month
                
                # Get 6-month history (excluding current month)
                history_start = (today.replace(day=1) - pd.DateOffset(months=6)).date()
                history_end = (today.replace(day=1) - pd.DateOffset(days=1)).date()
                
                history_mask = (df['Date'].dt.date >= history_start) & (df['Date'].dt.date <= history_end) & (df['Type'] == 'Expense')
                # Apply main account filter, but not category filter
                history_mask = history_mask & df['Account'].isin(selected_accounts)
                history_df = df[history_mask]
                
                if not history_df.empty:
                    # Group by month, then category, sum, then average
                    monthly_spend = history_df.groupby([pd.Grouper(key='Date', freq='MS'), 'Category'])['Amount'].sum().reset_index()
                    avg_spend = monthly_spend.groupby('Category')['Amount'].mean()
                    
                    current_spend = current_month_df.groupby('Category')['Amount'].sum()
                    
                    pacing_df = pd.DataFrame({'Current': current_spend, 'Average': avg_spend}).fillna(0)
                    pacing_df = pacing_df[pacing_df['Average'] > 0] # Only compare to categories we have an average for
                    
                    if not pacing_df.empty:
                        pacing_df['Pacing (%)'] = (pacing_df['Current'] / pacing_df['Average'])
                        
                        # Find categories spending faster than the month's progress (with a 20% tolerance)
                        over_pacing = pacing_df[pacing_df['Pacing (%)'] > (percent_of_month_passed + 0.20)]
                        over_pacing = over_pacing.sort_values(by='Pacing (%)', ascending=False).head(3)
                        
                        if not over_pacing.empty:
                            pacing_insights.append(f"**Spending Pace Alerts** (*{percent_of_month_passed*100:.0f}% of the month has passed*)")
                            for idx, row in over_pacing.iterrows():
                                pacing_insights.append(f"⚠️ **{idx}**: At {currency_symbol}{row['Current']:,.0f}, you've already spent {row['Pacing (%)']*100:.0f}% of your 6-month monthly average ({currency_symbol}{row['Average']:,.0f}).")
            
        except Exception as e:
            st.error(f"Error calculating insights: {e}") # Handle errors gracefully

        # Display Insights
        if not mom_insights_increases and not mom_insights_decreases and not pacing_insights:
            st.info(f"No significant spending changes or pacing alerts detected for **{selected_month_str}**. Keep up the good work!", icon="👍")
        else:
            col1, col2,col3 = st.columns(3)
            with col1:
                st.subheader(f"Month Learning Opportunities (vs. { last_month_start.strftime('%B %Y') })")
                if mom_insights_increases:
                    for insight_str in mom_insights_increases:
                        st.markdown(insight_str)
                else:
                    st.info("No significant MoM changes to report.")
            
            with col2:
                st.subheader(f"Month Wins (vs. { last_month_start.strftime('%B %Y') })")
                if mom_insights_decreases:
                    for insight_str in mom_insights_decreases:
                        st.markdown(insight_str)
                else:
                    st.info("No significant MoM changes to report.")
            
            with col3:
                st.subheader("Spending Pace (vs. 6-Mo. Avg)")
                if pacing_insights:
                    for insight_str in pacing_insights:
                        st.markdown(insight_str)
                else:
                    st.info("No pacing alerts to report. (Pacing only runs for the current, partial month).")


    # --- Visualizations (based on main filter) ---
    st.markdown("---")
    st.header("🎨 Visual Analysis")
    st.markdown("These visuals are based on your main filter selections at the top of the page.")

    if filtered_df.empty:
        st.info("No data to display for the main filters. Please adjust your date range, accounts, or categories.", icon="🧐")
        return # Stop here if there's nothing to visualize

    # Spending Trends Over Time with multiple views
    st.subheader("Spending Trends Over Time")
    st.markdown("Analyze your spending patterns from different perspectives. Do you spend more on weekends? Or at the beginning of the month?")

    # Create a consistent color map for categories to avoid repeats
    all_categories_in_df = sorted(filtered_df['Category'].unique())
    color_sequence = px.colors.qualitative.Plotly + px.colors.qualitative.G10 + px.colors.qualitative.Alphabet
    color_map = {category: color_sequence[i % len(color_sequence)] for i, category in enumerate(all_categories_in_df)}

    tab1, tab2, tab3, tab4 = st.tabs(["Daily Trend", "By Day of Week", "By Week of Month", "By Month"])

    with tab1:
        st.markdown("##### Daily Spending")
        st.markdown("This view shows your spending on a day-by-day basis, perfect for spotting specific days with high activity.")
        daily_spend = filtered_df.groupby([filtered_df['Date'].dt.date, 'Category'])['Amount'].sum().reset_index()
        if not daily_spend.empty:
            fig_daily_spend = px.bar(daily_spend, x='Date', y='Amount', color='Category', 
                                     labels={'Amount': 'Total Spend', 'Date': 'Date'},
                                     color_discrete_map=color_map)
            fig_daily_spend.update_layout(xaxis_title='Date', yaxis_title=f'Amount ({currency_symbol})', height=400)
            st.plotly_chart(fig_daily_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    with tab2:
        st.markdown("##### Spending by Day of the Week")
        st.markdown("Discover which days of the week you tend to spend the most. Are you a weekend spender or a weekday warrior?")
        weekday_df = filtered_df.copy()
        weekday_df['weekday'] = weekday_df['Date'].dt.day_name()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_df['weekday'] = pd.Categorical(weekday_df['weekday'], categories=weekday_order, ordered=True)
        spend_by_weekday = weekday_df.groupby(['weekday', 'Category'])['Amount'].sum().reset_index()
        if not spend_by_weekday.empty:
            fig_weekday_spend = px.bar(spend_by_weekday, x='weekday', y='Amount', color='Category', 
                                       labels={'Amount': 'Total Spend', 'weekday': 'Day of the Week'},
                                       color_discrete_map=color_map)
            fig_weekday_spend.update_layout(xaxis_title='Day of the Week', yaxis_title=f'Amount ({currency_symbol})', height=400)
            st.plotly_chart(fig_weekday_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    with tab3:
        st.markdown("##### Spending by Week of the Month")
        st.markdown("Does your spending change throughout the month? See if you spend more right after payday or towards the end of the month.")
        week_of_month_df = filtered_df.copy()
        week_of_month_df['week_of_month'] = (week_of_month_df['Date'].dt.day - 1) // 7 + 1
        spend_by_week = week_of_month_df.groupby(['week_of_month', 'Category'])['Amount'].sum().reset_index()
        if not spend_by_week.empty:
            fig_week_spend = px.bar(spend_by_week, x='week_of_month', y='Amount', color='Category', 
                                    labels={'Amount': 'Total Spend', 'week_of_month': 'Week of the Month'},
                                    color_discrete_map=color_map)
            fig_week_spend.update_layout(xaxis_title='Week of the Month', yaxis_title=f'Amount ({currency_symbol})', height=400)
            st.plotly_chart(fig_week_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    with tab4:
        st.markdown("##### Spending by Month")
        st.markdown("Compare your total spending across different months to identify seasonal trends or lifestyle changes over time.")
        month_df = filtered_df.copy()
        # Group by the actual month start date and category to ensure chronological order
        spend_by_month = month_df.groupby([pd.Grouper(key='Date', freq='MS'), 'Category'])['Amount'].sum().reset_index()
        spend_by_month['month_str'] = spend_by_month['Date'].dt.strftime('%B %Y') # Create a string representation for the labels
        if not spend_by_month.empty and spend_by_month['Amount'].sum() > 0:
            fig_month_spend = px.bar(spend_by_month, x='month_str', y='Amount', color='Category', 
                                     labels={'Amount': 'Total Spend', 'month_str': 'Month'},
                                     color_discrete_map=color_map)
            fig_month_spend.update_layout(xaxis_title='Month', yaxis_title=f'Amount ({currency_symbol})', height=400, xaxis={'tickangle': -45})
            st.plotly_chart(fig_month_spend, use_container_width=True)
        else:
            st.info("No data to display for this period.")

    # --- Category Deep Dive (Treemap & Summary) ---
    st.subheader("Category Deep Dive")
    st.markdown("Wondering where the bulk of your money goes? 🌳 These visuals make it crystal clear. The bigger the box, the bigger the spending category!")
    
    # Aggregate data for visuals
    category_summary_df = filtered_df.groupby('Category').agg(
        Total_Spend=('Amount', 'sum'),
        Transactions=('Amount', 'count'),
        Avg_Spend=('Amount', 'mean'),
        Most_Recent=('Date', 'max')
    ).reset_index()

    # --- RFM Analysis Summary Table ---
    st.markdown("##### Your Spending Habits at a Glance")
    st.markdown("This table summarizes your top categories based on total spending, frequency, and average purchase size.")
    
    # Use the aggregated df for the summary table
    summary_df = category_summary_df.sort_values(by='Total_Spend', ascending=False).head(5)
    summary_df['Avg_Spend'] = summary_df['Avg_Spend'].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    summary_df['Total_Spend'] = summary_df['Total_Spend'].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    summary_df['Most_Recent'] = summary_df['Most_Recent'].dt.strftime('%b %d, %Y')
    
    st.dataframe(
        summary_df.set_index('Category')[['Total_Spend', 'Transactions', 'Avg_Spend', 'Most_Recent']],
        use_container_width=True
    )

    # --- Treemap ---
    st.markdown("##### Expense Category Treemap")
    fig_treemap = go.Figure(go.Treemap(
        labels=category_summary_df['Category'],
        parents=[''] * len(category_summary_df),  # All categories stem from the root
        values=category_summary_df['Total_Spend'],
        marker_colorscale='Reds',
        # custom_data=['Frequency', 'Average'],
        textinfo="label+value"
    ))
    fig_treemap.update_layout(
        title_text='Expense Breakdown by Category',
        margin=dict(t=50, l=25, r=25, b=25)
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

    # --- Bubble Chart ---
    st.markdown("##### Category Spending Profile")
    st.markdown("This bubble chart helps you find different spending profiles. Are you making lots of small purchases (bottom-right) or a few big ones (top-left)?")
    
    # Use the same aggregated data
    fig_bubble = px.scatter(
        category_summary_df,
        x="Transactions",
        y="Avg_Spend",
        size="Total_Spend",
        color="Category",  # Color by category
        hover_name="Category",
        size_max=60,
        labels={
            "Transactions": "Number of Transactions (Frequency)",
            "Avg_Spend": f"Average Spend ({currency_symbol})",
            "Total_Spend": f"Total Spend ({currency_symbol})"
        }
    )
    fig_bubble.update_layout(
        title="Category Spending Profile (Frequency vs. Average Spend)",
        xaxis_title="Number of Transactions",
        yaxis_title=f"Average Spend ({currency_symbol})",
        showlegend=False # Hide legend as colors are just for distinction
    )
    st.plotly_chart(fig_bubble, use_container_width=True)


    # --- Full Transaction Table ---
    st.markdown("---")
    st.header("🧾 All Expense Transactions")
    st.markdown("Here is a complete list of all your expenses for the selected period. You can search and sort the table to find specific transactions.")
    
    # Format dataframe for display
    display_df = filtered_df[['Date', 'Category', 'Amount', 'Account']].copy()
    display_df['Amount'] = display_df['Amount'].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    expenses_page()

