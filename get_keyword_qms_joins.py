import os
import pandas as pd
from pathlib import Path

def ask_for_folder_path():
    """Ask user to provide folder path where CSV files can be found"""
    while True:
        folder_path = input("\nPlease enter the folder path where the CSV files are located: ").strip()
        
        # Remove quotes if user copied path with quotes
        if folder_path.startswith('"') and folder_path.endswith('"'):
            folder_path = folder_path[1:-1]
        elif folder_path.startswith("'") and folder_path.endswith("'"):
            folder_path = folder_path[1:-1]
        
        # Convert to Path object for easier handling
        path_obj = Path(folder_path)
        
        if not path_obj.exists():
            print(f"Error: The folder '{folder_path}' does not exist. Please try again.")
            continue
        
        if not path_obj.is_dir():
            print(f"Error: '{folder_path}' is not a directory. Please try again.")
            continue
        
        # Check if required CSV files exist
        required_files = [
            "22_keyword__c.csv",
            "10_qms_unit__c.csv", 
            "35_qms_unit_keywords_join__c.csv"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = path_obj / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            print(f"Error: The following required files are missing in '{folder_path}':")
            for missing_file in missing_files:
                print(f"  - {missing_file}")
            print("Please ensure all required files are present and try again.")
            continue
        
        return str(path_obj)

def load_csv_files(folder_path):
    """Load the three required CSV files into pandas DataFrames"""
    print("\nLoading CSV files...")
    
    try:
        # Load keyword CSV
        keyword_path = os.path.join(folder_path, "22_keyword__c.csv")
        df_keyword = pd.read_csv(keyword_path)
        print(f"✓ Loaded 22_keyword__c.csv: {len(df_keyword)} rows")
        
        # Load QMS unit CSV
        qms_unit_path = os.path.join(folder_path, "10_qms_unit__c.csv")
        df_qms_unit = pd.read_csv(qms_unit_path)
        print(f"✓ Loaded 10_qms_unit__c.csv: {len(df_qms_unit)} rows")
        
        # Load QMS unit keywords join CSV
        join_path = os.path.join(folder_path, "35_qms_unit_keywords_join__c.csv")
        df_join = pd.read_csv(join_path)
        print(f"✓ Loaded 35_qms_unit_keywords_join__c.csv: {len(df_join)} rows")
        
        return df_keyword, df_qms_unit, df_join
        
    except Exception as e:
        print(f"Error loading CSV files: {str(e)}")
        return None, None, None

def perform_joins(df_keyword, df_qms_unit, df_join):
    """Perform the specified left joins and return final dataframe"""
    print("\nPerforming data joins...")
    
    try:
        # First join: 35_qms_unit_keywords_join with 22_keyword on keyword__c = id
        print("Step 1: Joining join table with keyword table...")
        df_merged = pd.merge(
            df_join, 
            df_keyword, 
            left_on='keyword__c', 
            right_on='ignore.id', 
            how='left',
            suffixes=('_join', '_keyword')
        )
        print(f"✓ After keyword join: {len(df_merged)} rows")
        
        # Second join: result with 10_qms_unit on qms_unit__c = id  
        print("Step 2: Joining with QMS unit table...")
        df_final = pd.merge(
            df_merged,
            df_qms_unit,
            left_on='qms_unit__c',
            right_on='ignore.id',
            how='left',
            suffixes=('', '_qms')
        )
        print(f"✓ After QMS unit join: {len(df_final)} rows")
        

                 # Delete specified columns if they exist
        columns_to_delete = [
            'ignore.id_join',
            'qms_unit__c', 
            'keyword__c',
            'ignore.id_keyword',
            'ignore.id',
            'state__v_qms',
            'state__v',
            'is_valid__c'
        ]
        existing_columns_to_delete = [col for col in columns_to_delete if col in df_final.columns]
        if existing_columns_to_delete:
            df_final = df_final.drop(columns=existing_columns_to_delete)
            print(f"✓ Deleted columns: {existing_columns_to_delete}")

        df_final = df_final.rename(columns={
            'name__v':'keyword__c.name__v',
            'name__v_qms':'qms_unit__c.name__v'
            }
            )
        
       
        # Apply requested changes to final dataframe
        print("\nApplying final dataframe modifications...")
        
        final_columns_renamed = ['qms_unit__c.name__v', 'keyword__c.name__v', 'keyword_type__c']
       
        df_final = df_final[final_columns_renamed]
        
        print(f"✓ Final dataframe shape: {df_final.shape}")
        print(f"✓ Final columns: {list(df_final.columns)}")
        
        

        return df_final
        
    except Exception as e:
        print(f"Error performing joins: {str(e)}")
        return None

def display_results(df_final, folder_path):
    """Display results and statistics"""
    if df_final is None:
        print("No data to display due to previous errors.")
        return
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total rows in final dataset: {len(df_final)}")
    print(f"Total columns: {len(df_final.columns)}")
    
    # Automatically save the results to the specified filename in the same folder
    output_filename = "35_qms_unit_keywords_join__c_for_import.csv"
    output_path = os.path.join(folder_path, output_filename)
    
    try:
        df_final.to_csv(output_path, index=False)
        print(f"✓ Results automatically saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return
    
    # Show first few rows
    print(f"\nFirst 5 rows of the joined data:")
    print(df_final.head().to_string())
    
    # Show data types
    print(f"\nData types:")
    print(df_final.dtypes)

def create_keyword_qms_unit_joins():
    """Main function to create Keyword-QMS-Unit-Joins"""
    print("\n" + "="*60)
    print("CREATE KEYWORD-QMS-UNIT-JOINS")
    print("="*60)
    print("This function will:")
    print("1. Ask for folder path containing the required CSV files")
    print("2. Load the three CSV files into dataframes")
    print("3. Perform left joins to create a unified dataset")
    print("4. Display results with QMS unit names and keyword information")
    print("\nRequired files:")
    print("- 22_keyword__c.csv")
    print("- 10_qms_unit__c.csv")
    print("- 35_qms_unit_keywords_join__c.csv")
    
    try:
        # Step 1: Get folder path from user
        folder_path = ask_for_folder_path()
        
        # Step 2: Load CSV files
        df_keyword, df_qms_unit, df_join = load_csv_files(folder_path)
        
        if df_keyword is None or df_qms_unit is None or df_join is None:
            print("Failed to load CSV files. Operation aborted.")
            return
        
        # Step 3: Perform joins
        df_final = perform_joins(df_keyword, df_qms_unit, df_join)
        
        # Step 4: Display results
        display_results(df_final, folder_path)
        
        print(f"\n{'='*60}")
        print("Operation completed successfully!")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Operation failed.")

if __name__ == "__main__":
    create_keyword_qms_unit_joins()
