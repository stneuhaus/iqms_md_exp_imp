import os
import sys
import json
import csv
from datetime import datetime
import subprocess

def analyze_failure_files():
    """
    Display a menu of available failure files for analysis.
    """
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to import files directory
    imports_dir = os.path.join(script_dir, 'imports')
    if not os.path.exists(imports_dir):
        print("Imports directory not found!")
        return
    
    # Find all FAILURE.csv files
    failure_files = []
    for root, dirs, files in os.walk(imports_dir):
        for file in files:
            if file.upper().endswith('_FAILURE.CSV'):
                failure_files.append(os.path.join(root, file))
    
    # Get all .csv files from the input folder that might match
    input_dir = os.path.join(script_dir, 'input')
    csv_files = []
    if os.path.exists(input_dir):
        for file in os.listdir(input_dir):
            if file.lower().endswith('.csv'):
                csv_files.append(os.path.join(input_dir, file))
    
    if not failure_files:
        print("No failure files found!")
        return
    
    # Display menu of file options
    print("\nFailure files found:")
    for i, file in enumerate(failure_files, 1):
        print(f"{i}. {os.path.basename(file)}")
    
    # Get user selection
    try:
        choice = int(input("\nSelect a file to analyze (number), or 0 to exit: "))
        if choice == 0:
            return
        
        selected_file = failure_files[choice - 1]
        
        # Try to find corresponding input file
        selected_basename = os.path.basename(selected_file).replace('_FAILURE.csv', '')
        matching_input = None
        for csv_file in csv_files:
            if selected_basename in os.path.basename(csv_file):
                matching_input = csv_file
                break
        
        print(f"\nAnalyzing: {os.path.basename(selected_file)}")
        if matching_input:
            print(f"Found matching input file: {os.path.basename(matching_input)}")
            # Call analyse_failure from the analyse_failure.py script
            cmd = [sys.executable, os.path.join(script_dir, 'analyse_failure.py')]
            
            # Run in interactive mode 1 (single file analysis)
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Provide input to the script
            inputs = f"1\n{matching_input}\n{selected_file}\n"
            stdout, stderr = process.communicate(inputs)
            
            print(stdout)
            if stderr:
                print(f"Error: {stderr}")
        else:
            print("No matching input file found. Please specify the input file:")
            input_file = input("Path to input file: ").strip()
            if os.path.exists(input_file):
                # Call analyse_failure script
                cmd = [sys.executable, os.path.join(script_dir, 'analyse_failure.py')]
                
                # Run in interactive mode 1 (single file analysis)
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Provide input to the script
                inputs = f"1\n{input_file}\n{selected_file}\n"
                stdout, stderr = process.communicate(inputs)
                
                print(stdout)
                if stderr:
                    print(f"Error: {stderr}")
            else:
                print(f"Input file not found: {input_file}")
    
    except (ValueError, IndexError) as e:
        print(f"Invalid selection: {e}")
        return

def main_menu():
    """Display the main menu for analyzing failures"""
    while True:
        print("\nVault Loader Failure Analysis")
        print("1. Analyze Failure Files")
        print("0. Exit")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            analyze_failure_files()
        elif choice == "0":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main_menu()