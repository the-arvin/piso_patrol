import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils import add_currency_selector
import calendar # Needed for month calculations

st.set_page_config(
    page_title="Income Analysis",
    page_icon="💰",
    layout="wide"
)

def income_page():
    """
    This page provides a detailed analysis of the user's income.
    """
    add_currency_selector()
    currency_symbol = st.session_state.get("currency_symbol", "$")

    st.title("💰 Income Analysis")
    st.markdown("Let's review your earnings. This page helps you track your income sources and see how they trend over time.")

    if "processed_data" not in st.session_state or st.session_state.processed_data.empty:
        st.warning("We don't have any data to analyze yet! 📂 Please head over to the 'Data Mapping' page to upload and process your financial data first.", icon="⚠️")
        st.page_link("pages/2_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return

    df = st.session_state.processed_data
    # Ensure Date column is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # --- Data Filtering ---
    st.header("🗓️ Select Your Filters")
    st.markdown("Filter your income by date or account to focus your analysis.")
    
    with st.expander("Filters available here:", expanded=False):
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
                    start_date, end_date = min_date, max_date

        with col2:
            # --- Account Filtering ---
            all_accounts = sorted(df['Account'].unique())
            selected_accounts = st.multiselect("Filter by Account(s)", options=all_accounts, default=all_accounts)

        with col3:
            # --- Category Filtering (for Income) ---
            all_income_categories = sorted(df[df['Type'] == 'Income']['Category'].unique())
            if not all_income_categories:
                all_income_categories = []
            selected_categories = st.multiselect("Filter by Category(s)", options=all_income_categories, default=all_income_categories)


    # Apply all filters
    date_mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    account_mask = df['Account'].isin(selected_accounts)
    category_mask = df['Category'].isin(selected_categories)
    income_mask = df['Type'] == 'Income'

    filtered_df = df[date_mask & account_mask & category_mask & income_mask]

    if filtered_df.empty:
        st.info("No income transactions found for the selected filters.", icon="🧐")
        # Don't return, allow insights to run
        pass

    # --- Key Income Metrics ---
    st.markdown("---")
    st.header("📈 Income Metrics")
    st.markdown("Here are your top-line earnings for the *period selected above*.")

    if filtered_df.empty:
        st.info("No income transactions found for the selected filters.", icon="🧐")
    else:
        total_income = filtered_df['Amount'].sum()
        num_transactions = len(filtered_df)
        avg_income = filtered_df['Amount'].mean()
        largest_income = filtered_df['Amount'].max()

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Income", f"{currency_symbol}{total_income:,.2f}")
        kpi2.metric("Number of Income Events", f"{num_transactions}")
        kpi3.metric("Average Income", f"{currency_symbol}{avg_income:,.2f}")
        kpi4.metric("Largest Single Income", f"{currency_symbol}{largest_income:,.2f}")

    # --- Automated Insights Section ---
    st.markdown("---")
    st.header("💡 Automated Insights")
    st.markdown("Analyze your Year-to-Date (YTD) income trends. *Note: Insights are based on the Account and Category filters set above.*")

    ytd_insights = []
    today = datetime.now().date()
    
    # Create month selector for insights
    # We filter the DF for insights based on masks *except* date_mask
    income_df_for_insights = df[income_mask & account_mask & category_mask]
    
    if income_df_for_insights.empty:
        st.info("No income data available to generate insights.")
    else:
        # Create a list of available months in "Month YYYY" format
        available_months = income_df_for_insights['Date'].dt.to_period('M').unique()
        available_months = sorted(available_months, reverse=True)
        month_options = [month.strftime('%B %Y') for month in available_months]
        
        # Default to current month if available, otherwise most recent
        current_month_str = today.strftime('%B %Y')
        if current_month_str in month_options:
            default_index = month_options.index(current_month_str)
        else:
            default_index = 0 # Default to the most recent month
        
        selected_month_str = st.selectbox(
            "Select a month to analyze:",
            month_options,
            index=default_index,
            key="income_insight_month"
        )
        
        # --- Run Insight Calculations ---
        try:
            # 1. Year-to-Date (YTD) Insights
            selected_month_dt = datetime.strptime(selected_month_str, '%B %Y').date()
            
            # Get Selected Month's data
            insight_start_date = selected_month_dt.replace(day=1)
            _, last_day = calendar.monthrange(insight_start_date.year, insight_start_date.month)
            insight_end_date = insight_start_date.replace(day=last_day)
            
            current_month_mask = (income_df_for_insights['Date'].dt.date >= insight_start_date) & (income_df_for_insights['Date'].dt.date <= insight_end_date)
            current_month_df = income_df_for_insights[current_month_mask]

            # Get First Month's (Jan) data of the *same year*
            first_month_start = insight_start_date.replace(month=1, day=1)
            _, first_month_last_day = calendar.monthrange(first_month_start.year, 1)
            first_month_end = first_month_start.replace(day=first_month_last_day)
            
            first_month_mask = (income_df_for_insights['Date'].dt.date >= first_month_start) & (income_df_for_insights['Date'].dt.date <= first_month_end)
            first_month_df = income_df_for_insights[first_month_mask]
            
            # Aggregate
            current_month_income = current_month_df.groupby('Category')['Amount'].sum()
            first_month_income = first_month_df.groupby('Category')['Amount'].sum()

            comparison = pd.DataFrame({'Current': current_month_income, 'Previous': first_month_income}).fillna(0)
            comparison = comparison[(comparison['Previous'] > 0) | (comparison['Current'] > 0)] # Compare if income in either
            
            if not comparison.empty:
                comparison['Change (%)'] = ((comparison['Current'] - comparison['Previous']) / comparison['Previous']) * 100
                comparison = comparison.sort_values(by='Change (%)', ascending=False)
                
                # Replace inf with 100% for cases where Previous was 0
                comparison.replace([float('inf'), float('-inf')], 100.0, inplace=True) 

                top_increases = comparison[comparison['Change (%)'] > 10].head(3)
                top_decreases = comparison[comparison['Change (%)'] < -10].sort_values(by='Change (%)', ascending=True).head(3)

                if not top_increases.empty:
                    ytd_insights.append("**Top Increases:**")
                    for idx, row in top_increases.iterrows():
                        if row['Previous'] == 0:
                            ytd_insights.append(f"🔺 **{idx}**: {currency_symbol}{row['Current']:,.0f} (New income source this month)")
                        else:
                            ytd_insights.append(f"🔺 **{idx}**: {currency_symbol}{row['Current']:,.0f} (Up {row['Change (%)']:.0f}% from {currency_symbol}{row['Previous']:,.0f})")
                
                if not top_decreases.empty:
                    ytd_insights.append("**Top Decreases:**")
                    for idx, row in top_decreases.iterrows():
                        ytd_insights.append(f"🔻 **{idx}**: {currency_symbol}{row['Current']:,.0f} (Down {abs(row['Change (%)']):.0f}% from {currency_symbol}{row['Previous']:,.0f})")
            
        except Exception as e:
            st.error(f"Error calculating insights: {e}") # Handle errors gracefully

        # Display Insights
        if not ytd_insights:
            st.info(f"No significant YTD changes detected for **{selected_month_str}** compared to **January {selected_month_dt.year}**.", icon="👍")
        else:
            st.subheader(f"YTD Change (vs. January {selected_month_dt.year})")
            for insight_str in ytd_insights:
                st.markdown(insight_str)


    # --- Visualizations ---
    st.markdown("---")
    st.header("🎨 Visual Analysis")
    st.markdown("These visuals are based on your main filter selections at the top of the page.")

    if filtered_df.empty:
        st.info("No data to display for the main filters. Please adjust your date range, accounts, or categories.", icon="🧐")
        return # Stop here if there's nothing to visualize

    col1, col2 = st.columns(2)

    with col1:
        # Income Sources Breakdown (Pie Chart)
        st.subheader("Income Sources")
        st.markdown("What's bringing in the money? This chart shows the breakdown of your income by category.")
        category_income = filtered_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        
        if not category_income.empty:
            fig_pie = go.Figure(data=[go.Pie(
                labels=category_income.index,
                values=category_income.values,
                hole=.4,
                pull=[0.05] * len(category_income.index)
            )])
            fig_pie.update_layout(
                title_text='Income Breakdown by Category',
                height=400,
                legend_title='Category'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No income data to plot for this period.")

    with col2:
        # Income Trend Over Time (Bar Chart)
        st.subheader("Monthly Income Trend")
        st.markdown("How does your income change from month to month? This is great for spotting trends, bonuses, or raises.")
        
        # Group by month and category
        monthly_income_df = filtered_df.copy()
        monthly_income = monthly_income_df.groupby([pd.Grouper(key='Date', freq='MS'), 'Category'])['Amount'].sum().reset_index()
        monthly_income['month_str'] = monthly_income['Date'].dt.strftime('%B %Y')
        
        # Calculate total per month for percentages
        monthly_total = monthly_income.groupby('month_str')['Amount'].sum().to_dict()
        
        # Avoid division by zero if monthly_total is 0
        monthly_income['Percentage'] = monthly_income.apply(
            lambda row: (row['Amount'] / monthly_total[row['month_str']]) if monthly_total[row['month_str']] != 0 else 0, 
            axis=1
        )

        if not monthly_income.empty and monthly_income['Amount'].sum() > 0:
            fig_month_bar = px.bar(
                monthly_income, 
                x='month_str', 
                y='Amount', 
                color='Category',
                text=monthly_income.apply(lambda row: f"{currency_symbol}{row['Amount']:,.0f}<br>({row['Percentage']:.0%})", axis=1),
                labels={'Amount': 'Total Income', 'month_str': 'Month'},
                title="Monthly Income by Category"
            )
            fig_month_bar.update_layout(
                xaxis_title='Month', 
                yaxis_title=f'Amount ({currency_symbol})', 
                height=400, 
                xaxis={'tickangle': -45}
            )
            fig_month_bar.update_traces(textposition='inside')
            st.plotly_chart(fig_month_bar, use_container_width=True)
        else:
            st.info("No income data to plot for this period.")

    # --- Full Income Transaction Table ---
    st.markdown("---")
    st.header("🧾 All Income Transactions")
    st.markdown("Here is a complete list of all your income for the selected period.")
    
    display_df = filtered_df[['Date', 'Category', 'Amount', 'Account']].copy()
    display_df['Amount'] = display_df['Amount'].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    income_page()

