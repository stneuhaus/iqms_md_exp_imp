import os
import sys
import json
import csv
from datetime import datetime
import subprocess
import shutil

def analyze_failures():
    """Run the failure analysis script"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze_error_file.py")
    if os.path.exists(script_path):
        subprocess.run([sys.executable, script_path])
    else:
        print(f"Error: Analysis script not found at {script_path}")

def generate_report(config_path):
    """Generates and displays a report of the imports section."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    imports = config.get("imports", [])
    report_rows = []
    for import_config in imports:
        active = import_config.get("active", "")
        name = import_config.get("name", "")
        status = import_config.get("status", "")
        file_path = import_config.get("file_path", "")
        report_rows.append([active, name, status, file_path])

    # Print table to stdout
    print("\nImport Configuration Report")
    print("-" * 80)
    header = ["active", "name", "status", "file_path"]
    print("{:<8} {:<50} {:<15} {:<50}".format(*header))
    print("-" * 130)
    for row in report_rows:
        active_display = row[0]
        if str(active_display) == "1":
            active_display = "🟢"  # green circle
        elif str(active_display) == "0":
            active_display = "❌"  # red cross
        print("{:<8} {:<50} {:<15} {:<50}".format(active_display, row[1], row[2], row[3]))
    print("-" * 130)
    print("-" * 80)

    # Write CSV
    csv_filename = f"import_config_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(os.path.dirname(config_path), csv_filename)
    with open(csv_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["active", "name", "status", "file_path"])
        writer.writerows(report_rows)
    print(f"CSV report written to: {csv_path}\n")

def main_menu():
    """Main menu for the Vault Loader Import Utility"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "vault_loader_config.json")
    
    while True:
        print("\nVault Loader Import Utility")
        print("1. Start Import")
        print("2. Import Configuration Report")
        print("3. Activate all imports")
        print("4. Deactivate all imports")
        print("5. Analyze Failure Files")
        print("0. Exit")
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            from start_import_vault_loader import VaultImportRunner
            # Create VaultImport runner
            runner = VaultImportRunner()

            # Show overview of target vault and active loader files
            config = runner.config
            import_settings = config.get('import_settings', {})
            imports = config.get('imports', [])
            dns = import_settings.get('dns', '(not set)')
            print("\nTarget Vault (import_settings.dns):", dns)
            print("Active loader files (imports.name):")
            active_imports = [imp for imp in imports if imp.get('active', 1)]
            if active_imports:
                for imp in active_imports:
                    print("-", imp.get('name', '(no name)'))
            else:
                print("(None active)")
            # Ask user if program should proceed
            while True:
                proceed = input("\nProceed with import? (y/n): ").strip().lower()
                if proceed == 'y':
                    runner.run_all_imports()
                    break
                elif proceed == 'n':
                    print("Aborted by user.")
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        elif choice == "2":
            generate_report(config_path)
        elif choice == "3":
            # Activate all imports
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            imports = config.get('imports', [])
            for import_config in imports:
                import_config['active'] = 1
            # Backup
            backup_path = config_path + ".bak"
            shutil.copy2(config_path, backup_path)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            print(f"All imports activated. Backup saved as {backup_path}")
        elif choice == "4":
            # Deactivate all imports
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            imports = config.get('imports', [])
            for import_config in imports:
                import_config['active'] = 0
            # Backup
            backup_path = config_path + ".bak"
            shutil.copy2(config_path, backup_path)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            print(f"All imports deactivated. Backup saved as {backup_path}")
        elif choice == "5":
            analyze_failures()
        elif choice == "0":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main_menu()