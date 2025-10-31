import streamlit as st
import pandas as pd
import plotly.express as px
from utils import add_currency_selector

st.set_page_config(
    page_title="Stashes & Savings",
    page_icon="🍯",
    layout="wide"
)

def stashes_page():
    """
    This page allows the user to select expense categories to treat as 'stashes' (savings)
    and visualizes the total amount saved in those categories.
    """
    add_currency_selector()
    currency_symbol = st.session_state.get("currency_symbol", "$")

    # Initialize session state for goals and emojis if they don't exist
    if 'stash_goals' not in st.session_state:
        st.session_state.stash_goals = {}
    if 'stash_emojis' not in st.session_state:
        st.session_state.stash_emojis = {}

    st.title("🍯 Stashes & Savings Goals")
    st.markdown("This page is for tracking your progress on specific savings goals. Start by selecting which of your *expense categories* represent money you're stashing away (e.g., 'Vacation Fund', 'Car Savings Deposit').")

    if "processed_data" not in st.session_state or st.session_state.processed_data.empty:
        st.warning("We don't have any data to analyze yet! 📂 Please head over to the 'Data Mapping' page to upload and process your financial data first.", icon="⚠️")
        st.page_link("pages/2_Data_Mapping.py", label="Go to Data Mapping", icon="🗺️")
        return

    df = st.session_state.processed_data

    # Get all available *expense* categories to choose from
    all_expense_categories = sorted(df[df['Type'] == 'Expense']['Category'].unique())

    if not all_expense_categories:
        st.info("No expense categories were found in your data to select as stashes.", icon="ℹ️")
        return

    # --- Stash Category Selector, Goal Setting, and Emojis in Three Columns ---
    st.header("1. Select Stashes, Set Goals & Emojis")
    st.markdown("Choose categories to track, set your target goal, and pick an emoji for each.")
    
    col1, col2, col3 = st.columns([2,1,1])
    EMOJI_OPTIONS = ["🍯", "🏖️", "🚗", "🏠", "💻", "🎓", "💍", "🎁", "✈️", "💰", "🧑‍🎄", "🎉"]

    with col1:
        st.subheader("Select Categories")
        selected_stashes = st.multiselect(
            "Select categories to track as stashes:",
            options=all_expense_categories,
            default=None,
            label_visibility="collapsed" # Hide label as we have a subheader
        )

    with col2:
        st.subheader("Set Goals")
        if not selected_stashes:
            st.info("Select categories on the left to set goals.", icon="👈")
        else:
            # Use an expander to neatly contain the goal inputs
            with st.expander("Edit Goals", expanded=True):
                for category in selected_stashes:
                    # Get the existing goal from session state to populate the input
                    current_goal = st.session_state.stash_goals.get(category, 0.0)
                    
                    # Use st.number_input to get the goal. They will stack vertically.
                    goal = st.number_input(
                        f"Goal for {category}",
                        min_value=0.0,
                        value=current_goal,
                        step=100.0,
                        format="%.2f",
                        key=f"goal_{category}" # Unique key for state
                    )
                    # Update our central goal dictionary immediately
                    st.session_state.stash_goals[category] = goal

    with col3:
        st.subheader("Set Emojis")
        if not selected_stashes:
            st.info("Select categories on the left to set emojis.", icon="👈")
        else:
            # Use an expander to neatly contain the emoji inputs
            with st.expander("Edit Emojis", expanded=True):
                for category in selected_stashes:
                    # Get the existing emoji from session state
                    current_emoji = st.session_state.stash_emojis.get(category, "🍯")
                    # Get index of current emoji, default to 0 if not found
                    try:
                        current_index = EMOJI_OPTIONS.index(current_emoji)
                    except ValueError:
                        current_index = 0
                    
                    # Use st.selectbox to get the emoji
                    emoji = st.selectbox(
                        f"Emoji for {category}",
                        options=EMOJI_OPTIONS,
                        index=current_index,
                        key=f"emoji_{category}"
                    )
                    # Update our central emoji dictionary
                    st.session_state.stash_emojis[category] = emoji

    if not selected_stashes:
        st.info("Select one or more categories above to see your stashed savings.", icon="👆")
        return

    # Filter the dataframe for transactions matching the selected stash categories
    stash_df = df[df['Category'].isin(selected_stashes) & (df['Type'] == 'Expense')].copy()

    if stash_df.empty:
        st.info("No transactions found for the selected stash categories.", icon="ℹ️")
        return

    # --- Stash Analysis ---
    st.markdown("---")
    st.header("2. Your Savings Progress")
    st.markdown("Here's how much you've stashed away in total and for each goal.")

    # --- KPI: Total Stashed ---
    total_stashed = stash_df['Amount'].sum()
    st.metric("Total Stashed Away", f"{currency_symbol}{total_stashed:,.2f}")

    # --- Stash Cards ---
    st.subheader("Your Stash Cards")

    # Aggregate all data for the cards
    stash_table = stash_df.groupby('Category').agg(
        Total_Saved=('Amount', 'sum'),
        Contributions=('Amount', 'count'),
        Avg_Contribution=('Amount', 'mean'),
        Last_Contribution=('Date', 'max')
    ).reset_index()
    
    stash_table = stash_table.sort_values(by='Total_Saved', ascending=False)

    if stash_table.empty:
        st.info("No savings contributions found for the selected stashes.")
    else:
        # Create a dynamic grid of cards, 3 per row
        cols_per_row = 3
        cols = st.columns(cols_per_row)
        for i, row in enumerate(stash_table.iterrows()):
            data = row[1]
            col = cols[i % cols_per_row] # Cycle through the columns
            
            with col:
                # Create a bordered container for each card
                with st.container(border=True):
                    # --- Get the selected emoji ---
                    category_emoji = st.session_state.stash_emojis.get(data['Category'], "🍯")
                    st.subheader(f"{category_emoji} {data['Category']}")
                    
                    # --- Retrieve Goal and Calculate Attainment ---
                    goal_amount = st.session_state.stash_goals.get(data['Category'], 0.0)
                    total_saved = data['Total_Saved']
                    attainment_pct = 0.0
                    if goal_amount > 0:
                        attainment_pct = (total_saved / goal_amount)

                    # --- Display Metrics ---
                    st.metric(
                        label="Total Saved",
                        value=f"{currency_symbol}{total_saved:,.2f}"
                    )
                    
                    # --- NEW: Goal & Progress Section ---
                    if goal_amount > 0:
                        st.markdown(f"**Goal:** `{currency_symbol}{goal_amount:,.2f}`")
                        # Ensure progress doesn't go over 100%
                        progress_val = min(attainment_pct, 1.0) 
                        st.progress(progress_val, text=f"{attainment_pct*100:.1f}% Complete")
                    else:
                        st.markdown("**Goal:** `Not Set`")
                        st.progress(0, text="Set a goal to see progress")
                    
                    st.divider() # Visual separator

                    # Smaller metrics in columns
                    card_col1, card_col2 = st.columns(2)
                    with card_col1:
                        st.metric(
                            label="Contributions",
                            value=f"{data['Contributions']}"
                        )
                    with card_col2:
                         st.metric(
                            label="Avg. Contribution",
                            value=f"{currency_symbol}{data['Avg_Contribution']:,.2f}"
                        )
                    
                    st.divider() # Visual separator
                    
                    # Last contribution info
                    st.text(f"Last deposit: {data['Last_Contribution'].strftime('%Y-%m-%d')}")

    # --- Full Transaction Table ---
    st.markdown("---")
    st.header("🧾 All Stash Transactions")
    st.markdown("Here is a complete list of all your 'deposits' into these stashes.")
    st.dataframe(
        stash_df.sort_values(by='Date', ascending=False), 
        use_container_width=True, 
        hide_index=True
    )

if __name__ == "__main__":
    stashes_page()

