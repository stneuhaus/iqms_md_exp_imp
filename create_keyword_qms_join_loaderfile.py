import pandas as pd
import os
from datetime import datetime
from get_keyword_qms_joins import build_keyword_qms_unit_joins_from_folder


def _normalize_column_name(column_name):
    normalized = str(column_name).strip().lower()
    normalized = normalized.replace('ignore.', '')
    for ch in [' ', '.', '_', '-']:
        normalized = normalized.replace(ch, '')
    return normalized


def _get_candidate_columns(expected_column, available_columns, aliases=None):
    aliases = aliases or []
    expected_norm = _normalize_column_name(expected_column)
    wanted = [expected_column] + aliases

    candidates = []

    for candidate in wanted:
        if candidate in available_columns and candidate not in candidates:
            candidates.append(candidate)

    lower_map = {str(col).strip().lower(): col for col in available_columns}
    for candidate in wanted:
        key = str(candidate).strip().lower()
        if key in lower_map:
            mapped = lower_map[key]
            if mapped not in candidates:
                candidates.append(mapped)

    for column in available_columns:
        if _normalize_column_name(column) == expected_norm and column not in candidates:
            candidates.append(column)

    return candidates


def _resolve_required_column(df, dataframe_label, expected_column, aliases=None):
    columns = df.columns.tolist()

    if expected_column in columns:
        return expected_column

    candidates = _get_candidate_columns(expected_column, columns, aliases=aliases)

    print("\n" + "-" * 80)
    print(f"⚠ Required column '{expected_column}' not found in {dataframe_label}.")
    print(f"Available columns: {', '.join(columns)}")

    if candidates:
        print(f"Suggested alternative columns: {', '.join(candidates)}")

    while True:
        user_input = input(
            f"Map '{expected_column}' to which column? "
            "(enter name, number, or 'abort'): "
        ).strip()

        if user_input.lower() == 'abort':
            return None

        if user_input.isdigit():
            column_index = int(user_input) - 1
            if 0 <= column_index < len(columns):
                return columns[column_index]
            print(f"❌ Invalid selection '{user_input}'. Please select 1 to {len(columns)}.")
            continue

        if user_input in columns:
            return user_input

        for column in columns:
            if column.strip().lower() == user_input.strip().lower():
                return column

        print("❌ Column not found. You can paste the exact header, enter a number, or type 'abort'.")


def _apply_column_mapping(df, dataframe_label, mapping):
    for expected_column, selected_column in mapping.items():
        if selected_column is None:
            continue

        if expected_column == selected_column:
            continue

        if expected_column in df.columns:
            print(
                f"⚠ {dataframe_label}: '{expected_column}' already exists. "
                f"Keeping it and ignoring mapped column '{selected_column}'."
            )
            continue

        df = df.rename(columns={selected_column: expected_column})

    return df


def _resolve_and_apply_required_columns(df, dataframe_label, required_columns):
    mapping = {}

    for config in required_columns:
        expected = config['expected']
        aliases = config.get('aliases', [])
        selected = _resolve_required_column(df, dataframe_label, expected, aliases=aliases)

        if selected is None:
            print(f"❌ Aborted: required column '{expected}' could not be mapped for {dataframe_label}.")
            return None

        mapping[expected] = selected

    print(f"\nColumn mapping for {dataframe_label}:")
    for expected, selected in mapping.items():
        print(f"  - {expected} <- {selected}")

    df = _apply_column_mapping(df, dataframe_label, mapping)
    return df

def create_keyword_qms_join_loaderfile():
    """
    Creates a loader file by joining QMS unit data with keyword joins.
    
    This script:
    1. Loads the 35_qms_unit_keywords_join__c_for_import.csv file
    2. Loads the 10_qms_unit__c.csv file
    3. Loads the 22_keyword__c.csv file
    4. Joins the dataframes on matching name fields
    """
    
    print("=" * 80)
    print("Create Keyword-QMS-Unit Join Loader File")
    print("=" * 80)
    
    # Step 1: Build 35_qms_unit_keywords_join__c_for_import.csv from source vault export folder
    print("\nStep 1: Build keyword-QMS-unit join blueprint from source vault export folder.")
    print("-" * 40)
    source_folder = input(
        "Please enter the vault export folder path "
        "(e.g. C:\\souce_code\\iqms_md_exp_imp\\exports\\bayer-iqms.veevavault.com) "
        "where these CSV files are located: "
    ).strip()

    join_file_path = build_keyword_qms_unit_joins_from_folder(source_folder)
    if not join_file_path:
        print("❌ Error: Could not generate 35_qms_unit_keywords_join__c_for_import.csv from source folder.")
        return

    if not os.path.exists(join_file_path):
        print(f"❌ Error: Generated file not found: {join_file_path}")
        return
    
    # Step 2: Get folder path for QMS Unit and Keyword files
    print("\nStep 2: Locate the TARGET vault export folder to get IDs of QMS units and Keywords.")
    print("-" * 40)
    export_folder = input("Enter folder path containing 10_qms_unit__c.csv and 22_keyword__c.csv: ").strip()
    
    if not os.path.isdir(export_folder):
        print(f"❌ Error: Folder not found: {export_folder}")
        return
    
    qms_unit_file = os.path.join(export_folder, "10_qms_unit__c.csv")
    keyword_file = os.path.join(export_folder, "22_keyword__c.csv")
    
    # Validate files exist
    if not os.path.exists(qms_unit_file):
        print(f"❌ Error: File not found: {qms_unit_file}")
        return
    
    if not os.path.exists(keyword_file):
        print(f"❌ Error: File not found: {keyword_file}")
        return
    
    print(f"✓ Found join file: {join_file_path}")
    print(f"✓ Found QMS unit file: {qms_unit_file}")
    print(f"✓ Found keyword file: {keyword_file}")
    
    # Step 3: Load dataframes
    print("\nStep 3: Loading data files...")
    print("-" * 40)
    
    try:
        df_join = pd.read_csv(join_file_path, encoding='utf-8')
        print(f"✓ Loaded join file: {len(df_join)} rows")
        print(f"  Columns: {', '.join(df_join.columns.tolist())}")
        
        df_qms = pd.read_csv(qms_unit_file, encoding='utf-8')
        print(f"✓ Loaded QMS unit file: {len(df_qms)} rows")
        print(f"  Columns: {', '.join(df_qms.columns.tolist())}")
        
        df_keyword = pd.read_csv(keyword_file, encoding='utf-8')
        print(f"✓ Loaded keyword file: {len(df_keyword)} rows")
        print(f"  Columns: {', '.join(df_keyword.columns.tolist())}")
        
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        return

    # Resolve required columns (interactive fallback if exact header is missing)
    df_join = _resolve_and_apply_required_columns(
        df_join,
        "join file",
        [
            {'expected': 'keyword__c.name__v'},
            {'expected': 'keyword_type__c'},
            {'expected': 'qms_unit__c.name__v'}
        ]
    )
    if df_join is None:
        return

    df_qms = _resolve_and_apply_required_columns(
        df_qms,
        "QMS unit file",
        [
            {'expected': 'qms_unit__c.id', 'aliases': ['ignore.id', 'id']},
            {'expected': 'name__v'}
        ]
    )
    if df_qms is None:
        return

    df_keyword = _resolve_and_apply_required_columns(
        df_keyword,
        "keyword file",
        [
            {'expected': 'keyword__c.id', 'aliases': ['ignore.id', 'id']},
            {'expected': 'name__v'},
            {'expected': 'keyword_type__c'}
        ]
    )
    if df_keyword is None:
        return
    
    # Step 4: Perform join between df_qms and df_join
    print("\nStep 4: Joining data...")
    print("-" * 40)
    
    try:
        #create helper column by conctenating keyword__c.name__v and keyword_type__c in df_join
        df_join['keyword_helper'] = (
            df_join['keyword__c.name__v'].astype(str).str.strip()
            + "_"
            + df_join['keyword_type__c'].astype(str).str.strip()
        )

        #delete columns keyword__c.name__v and keyword_type__c from df_join
        df_join = df_join.drop(columns=['keyword__c.name__v', 'keyword_type__c'])


        #delet columns is_valid__c and state__v from df_qms
        df_qms = df_qms.drop(columns=['is_valid__c', 'state__v'], errors='ignore')
        # Join on name__v from 10_qms_unit__c.csv with qms_unit__c.name__v from join file
        print("Performing join: 10_qms_unit__c.name__v = 35_qms...qms_unit__c.name__v to get qms_unit__c.ignore.id")
        
        df_result = pd.merge(
            df_qms,
            df_join,
            left_on='name__v',
            right_on='qms_unit__c.name__v',
            how='left'
        )
        
        print(f"✓ Join completed: {len(df_result)} rows")
        
        #delete column name__v from df_result
        if 'name__v' in df_result.columns:
            df_result = df_result.drop(columns=['name__v'])


        

        # Check for any unmatched rows
        # unmatched = df_result[df_result['name__v'].isna()]
        # if len(unmatched) > 0:
        #     print(f"⚠ Warning: {len(unmatched)} rows from join file didn't match QMS units")
        # else:
        #     print(f"✓ All rows matched successfully")
        
    except Exception as e:
        print(f"❌ Error during join: {e}")
        return
    
   
    
    # Step 4: Join with keyword file
    print("\nStep 4b: Joining with keyword file...")
    print("-" * 40)
    
    try:
        # Join on keyword__c.name__v = name__v AND keyword_type__c = keyword_type__c
        print("Performing join: keyword__c.name__v = name__v AND keyword_type__c = keyword_type__c")

        # delte from df_keyword column state__v
        df_keyword = df_keyword.drop(columns=['state__v'], errors='ignore')

        #create helper column by conctenating name__v and keyword_type__c in df_keyword
        df_keyword['keyword_helper'] = (
            df_keyword['name__v'].astype(str).str.strip()
            + "_"
            + df_keyword['keyword_type__c'].astype(str).str.strip()
        )

        # delete columns name__v and keyword_type__c from df_keyword
        df_keyword = df_keyword.drop(columns=['name__v', 'keyword_type__c'])
                
        # Perform the join on both conditions
        df_result = pd.merge(
            df_result,
            df_keyword,
            left_on=['keyword_helper'],
            right_on=['keyword_helper'],
            how='left'
        )
        #delete rows whre keyword__c.id is NaN
        before_filter = len(df_result)
        df_result = df_result.dropna(subset=['keyword__c.id'])
        matched_rows = len(df_result)
        print(f"✓ Keyword ID matches: {matched_rows} / {before_filter}")
        if matched_rows == 0:
            print("⚠ Warning: 0 matched rows after keyword join. Check mapped columns and source values.")


        #rename columns in df_result
        df_result = df_result.rename(columns={
            'keyword__c.id': 'keyword__c',
            'qms_unit__c.id': 'qms_unit__c',
            'qms_unit__c.name__v': 'ignore.qms_unit__c.name__v',
            'keyword_helper': 'ignore.keyword_helper'}
            )
        
        print(f"✓ Keyword join completed: {len(df_result)} rows")
        # print(f"  Result columns: {', '.join(df_result.columns.tolist())}")
        # print(f"  First 5 rows:")
        # print(df_result.head())
       
        
    except Exception as e:
        print(f"❌ Error during keyword join: {e}")
        return
    
    # Step 5: Save output file
    print("\nStep 5: Saving output...")
    print("-" * 40)
    

    print(f"Output folder: {export_folder}" )
    output_file = os.path.join(
        export_folder,
        f"35_qms_unit_keywords_join__c.csv"
    )
    
    try:
        df_result.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Output saved to: {output_file}")
        print(f"  Total rows: {len(df_result)}")
        print(f"  Total columns: {len(df_result.columns)}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return
    
    # Step 6: Display summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"QMS unit rows:         {len(df_qms)}")
    print(f"Keyword rows:          {len(df_keyword)}")
    print(f"Result rows:           {len(df_result)}")
    print(f"Output file:           {output_file}")
    print("=" * 80)
    
    # Ask if user wants to see preview
    preview = input("\nShow preview of first 5 rows? (y/n): ").strip().lower()
    if preview == 'y':
        print("\nPreview of result:")
        print(df_result.head())

if __name__ == "__main__":
    create_keyword_qms_join_loaderfile()
