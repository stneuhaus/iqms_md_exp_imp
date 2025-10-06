import pandas as pd
import os
from datetime import datetime

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
    
    # Step 1: Get path to 35_qms_unit_keywords_join__c_for_import.csv
    print("\nStep 1: Locate the Keyword-QMS-Unit join file (will be used as blueprint).")
    print("-" * 40)
    join_file_path = input("Enter full path to 35_qms_unit_keywords_join__c_for_import.csv: ").strip()
    
    if not os.path.exists(join_file_path):
        print(f"❌ Error: File not found: {join_file_path}")
        return
    
    # Step 2: Get folder path for QMS Unit and Keyword files
    print("\nStep 2: Locate the export folder to get IDs of QMS units and Keywords of target vault.")
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
    
    # Step 4: Perform join between df_qms and df_join
    print("\nStep 4: Joining data...")
    print("-" * 40)
    
    try:
        #create helper column by conctenating keyword__c.name__v and keyword_type__c in df_join
        df_join['keyword_helper'] = df_join['keyword__c.name__v'] +"_"+ df_join['keyword_type__c']

        #delete columns keyword__c.name__v and keyword_type__c from df_join
        df_join = df_join.drop(columns=['keyword__c.name__v', 'keyword_type__c'])


        #delet columns is_valid__c and state__v from df_qms
        df_qms = df_qms.drop(columns=['is_valid__c', 'state__v'], errors='ignore')
        #rename columns ignore.id to qms_unit__c.id in df_qms
        df_qms = df_qms.rename(columns={'ignore.id': 'qms_unit__c.id'}, errors='ignore')

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
        df_keyword['keyword_helper'] = df_keyword['name__v'] +"_"+ df_keyword['keyword_type__c']

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
        #rename ignore.id to keyword__c.id in df_result
        if 'ignore.id' in df_result.columns:
            df_result = df_result.rename(columns={'ignore.id': 'keyword__c.id'})

        #delete rows whre keyword__c.id is NaN
        df_result = df_result.dropna(subset=['keyword__c.id'])


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
