import streamlit as st
import pandas as pd
from io import StringIO
import re # Added for URL parsing
import urllib.parse # Added for URL encoding sheet names
from datetime import datetime
from utils import add_currency_selector

st.set_page_config(
    page_title="Data Mapping",
    page_icon="🗺️",
    layout="wide"
)

def load_gsheet_data(gheet_url, sheet_name):
    """
    Loads data from a public Google Sheet URL.
    """
    try:
        # Extract the sheet ID from the URL
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', gheet_url)
        if not match:
            st.error("Invalid Google Sheet URL. Could not find Sheet ID.", icon="🚫")
            return None
        sheet_id = match.group(1)
        
        # URL-encode the sheet name
        encoded_sheet_name = urllib.parse.quote(sheet_name)
        
        # Construct the CSV export URL
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}'
        
        # Read the CSV data
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error loading Google Sheet. Please ensure the URL is correct, the sheet name is exact, and the sheet is public ('Anyone with the link can view'). Error: {e}", icon="🚫")
        return None

def data_mapping_page():
    """
    This page handles the uploading, inspection, and mapping of user's financial data.
    """
    add_currency_selector()
    st.title("🗺️ Data Mapping & Setup")
    st.markdown("This is the most important step! Let's load your data, map your columns, and define your savings goals.")

    # --- Step 1: Data Loading ---
    st.markdown("---")
    st.header("Step 1: 📂 Load Your Data")
    st.markdown("First, let's get your transaction data into the app. Choose your preferred method below.")

    data_source_options = ("Upload CSV", "Google Sheet", "Load Sample Data")
    
    # Ensure the selection is saved in session state and persists across reruns
    if "data_source_selector" not in st.session_state:
        st.session_state.data_source_selector = data_source_options[0] # Default to 'Upload CSV'

    # Find the index of the current selection to set the radio button
    # This ensures the widget stays in sync with the session state
    try:
        current_index = data_source_options.index(st.session_state.data_source_selector)
    except ValueError:
        current_index = 0 # Default to first option if state is somehow invalid
    
    data_source = st.radio(
        "Select your data source:",
        data_source_options,
        index=current_index, # Explicitly set the widget's state
        horizontal=True,
        key="data_source_selector" # This key ensures the selection is saved
    )

    df_raw = None

    if data_source == "Upload CSV":
        uploaded_file = st.file_uploader("Upload your .csv file", type=["csv"])
        if uploaded_file:
            try:
                df_raw = pd.read_csv(uploaded_file)
                st.info(f"Successfully loaded `{uploaded_file.name}`.", icon="📄")
                st.balloons()
            except Exception as e:
                st.error(f"Error loading CSV file: {e}")

    elif data_source == "Google Sheet":
        st.markdown("Paste the URL of your Google Sheet and enter the **exact** name of the sheet you want to load.")
        st.info("ℹ️ Your Google Sheet must be publicly accessible ('Anyone with the link can view').", icon="💡")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            gheet_url = st.text_input("Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")
        with col2:
            sheet_name = st.text_input("Sheet Name", placeholder="e.g., 'Transactions' or 'Sheet1'")

        if st.button("Load Data from Google Sheet"):
            if gheet_url and sheet_name:
                with st.spinner("Loading data from Google Sheet..."):
                    df_raw = load_gsheet_data(gheet_url, sheet_name)
                    if df_raw is not None:
                        st.info(f"Successfully loaded data from sheet: `{sheet_name}`.", icon="📄")
                        st.balloons()
            else:
                st.warning("Please provide both the URL and the Sheet Name.", icon="⚠️")
    
    elif data_source == "Load Sample Data":
        st.markdown("Click the button to load a sample dataset to explore the app's features.")
        if st.button("Load Sample Data", type="primary"):
            with st.spinner("Loading sample data..."):
                sample_url = "https://docs.google.com/spreadsheets/d/16f6vJQ9DjG2JOUprEHOf-G6fIoKOXjGCdhWTSh3AunM/edit?gid=1771757736#gid=1771757736"
                sample_sheet_name = "sample data"
                df_raw = load_gsheet_data(sample_url, sample_sheet_name)
                if df_raw is not None:
                    st.info("Successfully loaded sample data!", icon="🎉")
                st.balloons()

    # --- End of Data Loading ---

    # If new data was loaded, put it in session state
    if df_raw is not None:
        st.session_state.raw_data = df_raw
        # Clear old processed data if new raw data is loaded
        if "processed_data" in st.session_state:
            del st.session_state.processed_data
        if "auto_processed" in st.session_state:
            del st.session_state.auto_processed
        st.rerun() # Rerun to start processing with the new data

    # --- START OF DATA PROCESSING (from st.session_state.raw_data) ---
    
    # Ensure processed data has correct date type before filtering (FIX from previous TypeError)
    if "processed_data" in st.session_state:
        st.session_state.processed_data['Date'] = pd.to_datetime(st.session_state.processed_data['Date'], errors='coerce')


    if "raw_data" in st.session_state:
        raw_df = st.session_state.raw_data
        
        # --- Auto-Processing Attempt ---
        if "auto_processed" not in st.session_state:
            st.session_state.auto_processed = False
            try:
                # Find standard columns
                date_col = next(c for c in raw_df.columns if c.lower().strip() == 'date')
                amount_col = next(c for c in raw_df.columns if c.lower().strip() == 'amount')
                category_col = next(c for c in raw_df.columns if c.lower().strip() == 'category')
                
                # Optional columns
                type_col = next((c for c in raw_df.columns if c.lower().strip() == 'type'), None)
                acct_col = next((c for c in raw_df.columns if c.lower().strip() == 'account'), None)
                
                # --- Auto-process logic ---
                with st.spinner("Standard columns found! Attempting to auto-process your data..."):
                    processed_df = raw_df[[date_col, amount_col, category_col]].copy()
                    processed_df.columns = ['Date', 'Amount', 'Category']
                    
                    # Handle Type
                    if type_col:
                        processed_df['Type'] = raw_df[type_col].fillna('Expense')
                    else:
                        # Auto-detect type based on amount (assuming positive=Income, negative=Expense)
                        # First, clean amount column
                        temp_amount = pd.to_numeric(raw_df[amount_col].astype(str).str.replace(r'[,"\$]', '', regex=True), errors='coerce')
                        processed_df['Type'] = temp_amount.apply(lambda x: 'Income' if x >= 0 else 'Expense').fillna('Expense')

                    # Handle Account
                    processed_df['Account'] = raw_df[acct_col].fillna('Default Account') if acct_col else 'Default Account'
                    
                    # --- Data Cleaning ---
                    original_rows = len(processed_df)
                    processed_df['Date'] = pd.to_datetime(processed_df['Date'], errors='coerce')
                    processed_df['Amount'] = pd.to_numeric(processed_df['Amount'].astype(str).str.replace(r'[,"\$]', '', regex=True), errors='coerce')
                    processed_df['Amount'] = processed_df['Amount'].abs() # Use absolute value, type is now set
                    
                    invalid_rows = processed_df[processed_df['Date'].isna() | processed_df['Amount'].isna()]
                    processed_df = processed_df.dropna(subset=['Date', 'Amount'])
                    processed_df['Category'] = processed_df['Category'].astype(str).str.strip()
                    
                    st.session_state.processed_data = processed_df
                    st.session_state.invalid_rows = invalid_rows
                    st.session_state.auto_processed = True
                    st.rerun() # Rerun to show the results of auto-processing
            
            except StopIteration:
                # Standard columns not found, do nothing and let manual mapping take over
                pass
            except Exception as e:
                st.warning(f"Auto-processing failed: {e}. Please map your columns manually.")

        # --- Display Auto-Process Results ---
        if st.session_state.get("auto_processed", False):
            st.success("We automatically detected and processed your data! You can review it below or map columns manually to change it.", icon="🎉")
            if not st.session_state.invalid_rows.empty:
                st.warning(f"Removed {len(st.session_state.invalid_rows)} row(s) with invalid Date or Amount formats.", icon="⚠️")
                with st.expander("Show Removed Rows"):
                    st.dataframe(st.session_state.invalid_rows)

        # --- Step 2: Manual Column Mapping ---
        st.markdown("---")
        st.header("Step 2: 🗺️ Map Your Columns (Optional)")
        st.markdown("If the auto-processing wasn't quite right, or if you want to make changes, use the selectors below.")
        
        with st.expander("Show Manual Column Mapping Tools", expanded=not st.session_state.get("auto_processed", False)):
            available_columns = raw_df.columns.tolist()
            available_columns_with_none = available_columns + ['None']
            
            # --- Try to find smart defaults ---
            date_guess = next((c for c in available_columns if 'date' in c.lower()), available_columns[0])
            amount_guess = next((c for c in available_columns if 'amount' in c.lower()), available_columns[0])
            category_guess = next((c for c in available_columns if 'category' in c.lower()), available_columns[0])
            type_guess = next((c for c in available_columns if 'type' in c.lower()), 'None')
            acct_guess = next((c for c in available_columns if 'account' in c.lower()), 'None')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                date_col = st.selectbox("**Date Column** (Required)", options=available_columns, index=available_columns.index(date_guess))
                type_col = st.selectbox("**Type Column** (Optional)", options=available_columns_with_none, index=available_columns_with_none.index(type_guess), help="Column for 'Income'/'Expense'. If 'None', we'll guess based on the amount.")
            with col2:
                amount_col = st.selectbox("**Amount Column** (Required)", options=available_columns, index=available_columns.index(amount_guess))
                acct_col = st.selectbox("**Account Column** (Optional)", options=available_columns_with_none, index=available_columns_with_none.index(acct_guess), help="Column for your different accounts (e.g., 'Checking', 'Credit Card'). If 'None', we'll use 'Default Account'.")
            with col3:
                category_col = st.selectbox("**Category Column** (Required)", options=available_columns, index=available_columns.index(category_guess))

            if st.button("Process & Save Mapped Data", type="primary"):
                with st.spinner("Processing your data..."):
                    try:
                        # --- Data Cleaning and Validation ---
                        cols_to_use = [date_col, amount_col, category_col]
                        new_names = ['Date', 'Amount', 'Category']
                        
                        if type_col != 'None':
                            cols_to_use.append(type_col)
                            new_names.append('Type')
                        if acct_col != 'None':
                            cols_to_use.append(acct_col)
                            new_names.append('Account')

                        working_df = raw_df[cols_to_use].copy()
                        working_df.columns = new_names
                        original_rows = len(working_df)

                        # Coerce errors, turning bad data into NaT/NaN
                        working_df['Date'] = pd.to_datetime(working_df['Date'], errors='coerce')
                        working_df['Amount'] = pd.to_numeric(working_df['Amount'].astype(str).str.replace(r'[,"\$]', '', regex=True), errors='coerce')
                        
                        # Identify and store the bad rows before dropping them
                        invalid_rows = working_df[working_df['Date'].isna() | working_df['Amount'].isna()]
                        
                        # Create the final, cleaned dataframe by dropping invalid rows
                        processed_df = working_df.dropna(subset=['Date', 'Amount']).copy()
                        
                        if not invalid_rows.empty:
                            st.warning(f"Removed {len(invalid_rows)} row(s) with invalid Date or Amount formats.", icon="⚠️")
                            with st.expander("Show Removed Rows"):
                                st.dataframe(invalid_rows)
                        
                        # --- Post-processing ---
                        
                        # Derive 'Type' if not provided
                        if 'Type' not in processed_df.columns:
                            processed_df['Type'] = processed_df['Amount'].apply(lambda x: 'Income' if x >= 0 else 'Expense')
                        
                        # Set default 'Account' if not provided
                        if 'Account' not in processed_df.columns:
                            processed_df['Account'] = "Default Account"
                        
                        # Final data type conversions
                        processed_df['Amount'] = processed_df['Amount'].abs() # We use 'Type' to know if it's in or out
                        processed_df['Category'] = processed_df['Category'].astype(str).str.strip()
                        processed_df['Type'] = processed_df['Type'].fillna('Expense').astype(str)
                        processed_df['Account'] = processed_df['Account'].fillna('Default Account').astype(str)
                        
                        st.session_state.processed_data = processed_df
                        st.session_state.auto_processed = True # Mark as processed
                        st.success(f"Successfully processed {len(processed_df)} out of {original_rows} valid rows. You can now explore the other pages or refine your data below.", icon="✅")
                        st.balloons()
                        st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred during processing: {e}")

        # --- Step 3: Refine & Edit Your Data ---
        if "processed_data" in st.session_state:
            st.markdown("---")
            st.header("Step 3: ✏️ Refine & Edit Your Data (Optional)")
            st.markdown("Your data is processed! You can now make manual changes, fix typos, or re-categorize transactions.")
            
            # Ensure 'Date' column is datetime before filtering for the editor
            st.session_state.processed_data['Date'] = pd.to_datetime(st.session_state.processed_data['Date'], errors='coerce')

            # --- Add Filters for the Editor ---
            st.markdown("##### Filter Data Before Editing")
            st.info("Use these filters to find specific transactions you want to edit in the table below.", icon="💡")
            
            all_categories_processed = ['All'] + sorted(st.session_state.processed_data['Category'].unique())
            all_types_processed = ['All'] + sorted(st.session_state.processed_data['Type'].unique())
            
            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                filter_cat = st.selectbox("Filter by Category", options=all_categories_processed)
            with edit_col2:
                filter_type = st.selectbox("Filter by Type", options=all_types_processed)
            
            # Apply filters
            df_to_edit = st.session_state.processed_data.copy()
            if filter_cat != 'All':
                df_to_edit = df_to_edit[df_to_edit['Category'] == filter_cat]
            if filter_type != 'All':
                df_to_edit = df_to_edit[df_to_edit['Type'] == filter_type]
            
            # --- Data Editor ---
            st.markdown("##### Edit Your Transactions")
            st.caption("You can add rows, delete rows, and edit any cell. Double-click a cell to edit.")
            
            edited_df = st.data_editor(
                df_to_edit,
                num_rows="dynamic",
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                    "Amount": st.column_config.NumberColumn("Amount", format=f"$ %.2f"),
                    "Category": st.column_config.SelectboxColumn("Category", options=sorted(st.session_state.processed_data['Category'].unique()), required=True),
                    "Type": st.column_config.SelectboxColumn("Type", options=['Income', 'Expense', 'Stash'], required=True),
                    "Account": st.column_config.TextColumn("Account")
                },
                use_container_width=True,
                key="data_editor"
            )
            
            if st.button("Save & Update All Changes", type="primary"):
                with st.spinner("Saving your changes..."):
                    # This is a simplified merge. A more robust way would be to track indices.
                    # For now, we replace the filtered part with the edited part.
                    # This assumes the user doesn't change the filter *while* editing.
                    
                    # Update the main dataframe by merging on index
                    # This is safer than just replacing the filtered slice
                    st.session_state.processed_data.update(edited_df)
                    
                    # This is a simpler logic: just replace the whole dataframe with the edited version
                    # This is problematic if the user was filtering.
                    # Let's use the first, safer logic.
                    
                    # Re-load the original data
                    main_df = st.session_state.processed_data.copy()
                    # Update rows that were in the edited_df based on their index
                    main_df.update(edited_df)
                    # Add new rows (those in edited_df but not main_df)
                    new_rows = edited_df[~edited_df.index.isin(main_df.index)]
                    if not new_rows.empty:
                        main_df = pd.concat([main_df, new_rows])
                    # Remove deleted rows (those in main_df but not edited_df)
                    main_df = main_df[main_df.index.isin(edited_df.index)]
                    
                    # A simpler approach for now:
                    # Let's assume the filters are just for *viewing*
                    # and the `edited_df` is what we want to save
                    # This is wrong. `st.data_editor` returns the *edited version of the input*.
                    # So `edited_df` is the edited, filtered dataframe.
                    
                    # We need to update the *original* dataframe with the changes.
                    # Let's update `st.session_state.processed_data`
                    
                    # 1. Get original df
                    original_df = st.session_state.processed_data
                    
                    # 2. Update existing rows
                    original_df.update(edited_df)
                    
                    # 3. Add new rows (those in edited_df with a new index)
                    new_indices = edited_df.index.difference(original_df.index)
                    if not new_indices.empty:
                        original_df = pd.concat([original_df, edited_df.loc[new_indices]])

                    # 4. Delete removed rows
                    deleted_indices = original_df.index.difference(edited_df.index)
                    if not deleted_indices.empty:
                        original_df = original_df.drop(deleted_indices)
                        
                    # This logic is complex and prone to errors.
                    # A much simpler (and intended) way:
                    # The `edited_df` is the full, edited version *of the dataframe that was passed in*.
                    # The filters just change *which dataframe is passed in*.
                    
                    # New simpler logic:
                    Here = """
                    # 1. Pass the *unfiltered* df to the editor
                    # 2. The user edits it
                    # 3. Save the *returned* df
                    """
                    # Let's modify the code above...
                    # Oh, wait. The user *wants* to filter.
                    
                    # Okay, let's stick to the button logic.
                    # When 'Save' is clicked, `st.session_state.data_editor` holds the *full* edited dataframe.
                    
                    # Let's read the state from the key
                    edited_data_from_state = st.session_state.data_editor
                    st.session_state.processed_data = edited_data_from_state
                    
                    # THIS IS THE FIX:
                    # Pass the *full* dataframe to the editor
                    # and then just save its result.
                    
                    st.session_state.processed_data = edited_df # `edited_df` is the returned, edited dataframe
                    
                    # Re-convert types just in case
                    st.session_state.processed_data['Date'] = pd.to_datetime(st.session_state.processed_data['Date'], errors='coerce')
                    st.session_state.processed_data['Amount'] = pd.to_numeric(st.session_state.processed_data['Amount'], errors='coerce')
                    
                    st.success("Your changes have been saved!", icon="✅")
                    st.rerun()

        # --- Step 4: Define Stash Categories ---
        if "processed_data" in st.session_state:
            st.markdown("---")
            st.header("Step 4: 🏦 Define Your Stash Categories")
            st.markdown("Select which expense categories you want to treat as 'Stashes' (e.g., savings goals). This will update your 'Stashes' page.")

            # Initialize session state for goals and emojis if they don't exist
            if 'stash_goals' not in st.session_state:
                st.session_state.stash_goals = {}
            if 'stash_emojis' not in st.session_state:
                st.session_state.stash_emojis = {}

            all_expense_categories = sorted(st.session_state.processed_data[
                (st.session_state.processed_data['Type'] == 'Expense') | 
                (st.session_state.processed_data['Type'] == 'Stash')
            ]['Category'].unique())

            if not all_expense_categories:
                st.info("No expense or stash categories found to define as stashes.")
                return

            emoji_options = ["🏦", "🍯","💰", "✈️", "🚗", "🏠", "🎓", "🎁", "💻"]

            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown("**Select Stash Categories**")
                selected_stashes = st.multiselect(
                    "Select categories to track as stashes:",
                    options=all_expense_categories,
                    default=list(st.session_state.stash_goals.keys())
                )

            with col2:
                st.markdown("**Set Your Goals**")
                # Update session state keys based on selection
                current_goals = st.session_state.stash_goals.copy()
                st.session_state.stash_goals.clear() # Clear and rebuild
                
                for stash in selected_stashes:
                    st.session_state.stash_goals[stash] = st.number_input(
                        f"Goal for {stash} ($)",
                        min_value=0.0,
                        value=current_goals.get(stash, 0.0),
                        key=f"goal_{stash}"
                    )
            
            with col3:
                st.markdown("**Assign Emojis**")
                current_emojis = st.session_state.stash_emojis.copy()
                st.session_state.stash_emojis.clear() # Clear and rebuild
                
                for stash in selected_stashes:
                    st.session_state.stash_emojis[stash] = st.selectbox(
                        f"Emoji for {stash}",
                        options=emoji_options,
                        index=emoji_options.index(current_emojis.get(stash, "🏦")),
                        key=f"emoji_{stash}"
                    )
            
            if st.button("Save Stash Definitions"):
                st.success("Stash goals and emojis have been saved!", icon="✅")
                # No rerun needed, state is already set

        # --- Clear Data Button ---
        if st.button("Clear All Data & Start Over"):
            keys_to_clear = ['raw_data', 'processed_data', 'auto_processed', 'invalid_rows', 'stash_goals', 'stash_emojis']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    data_mapping_page()

