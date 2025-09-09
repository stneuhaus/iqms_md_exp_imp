import subprocess
import sys
import os
import json
import shutil
import csv
from datetime import datetime

class VaultLoaderRunner:
    def __init__(self, config_file='config/vault_loader_config.json'):
        # Get the directory where this script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.script_dir, config_file)
        self.config = {}
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.load_config()
        self.setup_log_directories()
        
    def setup_log_directories(self):
        """Create log directories if they don't exist"""
        logs_dir = os.path.join(self.script_dir, 'logs')
        os.makedirs(os.path.join(logs_dir, 'success'), exist_ok=True)
        os.makedirs(os.path.join(logs_dir, 'failure'), exist_ok=True)
        
    def load_config(self):
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_file):
            print(f"Config file {self.config_file} not found!")
            sys.exit(1)
        
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)
    
    def load_password(self, password_param):
        """Load password from file or return direct password"""
        # Check if password_param is a file path (relative to config folder if not absolute)
        if not os.path.isabs(password_param):
            password_file = os.path.join(self.script_dir, 'config', password_param)
        else:
            password_file = password_param
            
        if os.path.exists(password_file):
            try:
                with open(password_file, 'r', encoding='utf-8') as f:
                    password = f.read().strip()
                print(f"Password loaded from file: {password_file}")
                return password
            except Exception as e:
                print(f"Error reading password file {password_file}: {e}")
                sys.exit(1)
        else:
            # Assume it's a direct password
            print("Using direct password from configuration")
            return password_param
    
    def log_skipped(self, export_config):
        """Log skipped export to success log"""
        success_log = os.path.join(self.script_dir, 'logs', 'success', f'success_{self.run_timestamp}.csv')
        
        # Extract object name from params
        params = export_config['params'].split()
        object_name = ""
        if '-export' in params:
            export_index = params.index('-export')
            if export_index + 1 < len(params):
                object_name = params[export_index + 1]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(success_log), exist_ok=True)
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.exists(success_log)
        
        with open(success_log, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['file_name', 'object_name', 'row_count', 'timestamp'])
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(['SKIPPED', object_name, 'N/A', timestamp])
    
    def run_java_command(self, export_config):
        """Execute the Java VaultLoader with given parameters"""
        
        # Check if export is active
        active = export_config.get('active', 1)  # Default to 1 (active) if not specified
        if active == 0:
            print(f"⏭️ Skipping '{export_config['name']}' (inactive)")
            self.log_skipped(export_config)
            return True  # Return True to indicate successful skip
        
        # Get general configuration
        general = self.config['general']
        export_settings = self.config.get('export_settings', {})
        java_exe = general['java_exe']
        vault_loader_path = general['vault_loader']
        # Make vault_loader path absolute if it's relative
        if not os.path.isabs(vault_loader_path):
            vault_loader = os.path.join(self.script_dir, vault_loader_path)
        else:
            vault_loader = vault_loader_path
        dns = export_settings.get('dns', '')
        username = export_settings.get('username', '')
        password_param = export_settings.get('password', '')
        password = self.load_password(password_param)
        downloadpath = general.get('downloadpath', '')
        
        # Make downloadpath absolute if it's relative
        if downloadpath and not os.path.isabs(downloadpath):
            downloadpath = os.path.join(self.script_dir, downloadpath)
        
        # Build Java command with dns, username and password parameters
        java_command = [java_exe, '-jar', vault_loader]
        
        # Add DNS parameter if present
        if dns:
            java_command.extend(['-dns', dns])
        
        # Add username and password
        java_command.extend(['-u', username, '-p', password])
        
        # Add export parameters
        params = export_config['params'].split()
        java_command.extend(params)
        
        # Add where parameter if present
        where_clause = export_config.get('where', '')
        if where_clause:
            java_command.extend(['-where', where_clause])
        
        # Add downloadpath parameter if present
        if downloadpath:
            java_command.extend(['-downloadpath', downloadpath])
        
        # Add optional columns parameter if present
        columns = export_config.get('columns', [])
        if columns:
            java_command.extend(['-columns', ','.join(columns)])
        
        print(f"🚀 Starting Java process for: {export_config['name']}")
        # Build display command (hide password)
        display_params = params.copy()
        if where_clause:
            display_params.extend(['-where', where_clause])
        if downloadpath:
            display_params.extend(['-downloadpath', downloadpath])
        if columns:
            display_params.extend(['-columns', ','.join(columns)])
        
        dns_display = f"-dns {dns} " if dns else ""
        command_display = f"{java_exe} -jar {vault_loader} {dns_display}-u {username} -p [HIDDEN] {' '.join(display_params)}"
        print(f"Command: {command_display}")
        
        # Start process
        try:
            process = subprocess.Popen(
                java_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.script_dir
            )
            
            # Get output
            stdout, stderr = process.communicate(timeout=6000)  # 100 minute timeout
            
            print("Output:")
            print(stdout)
            if stderr:
                print("Errors:")
                print(stderr)
            
            return_code = process.returncode
            print(f"Process completed with return code: {return_code}")
            
            # Check if stdout contains more than the standard header
            expected_header = "Vault Loader. (c)Veeva Systems 2014-2021. All rights reserved."
            if stdout and stdout.strip() != expected_header:
                # If there's additional content beyond the header, log it as an error
                additional_output = stdout.strip()
                if additional_output.startswith(expected_header):
                    # Remove the header and check if there's additional content
                    remaining_output = additional_output[len(expected_header):].strip()
                    if remaining_output:
                        print(f"Warning: Additional output detected: {remaining_output}")
                        self.log_failure(export_config, f"Additional output: {remaining_output}")
                        return False
                elif additional_output != expected_header:
                    # Completely different output
                    print(f"Warning: Unexpected output: {additional_output}")
                    self.log_failure(export_config, f"Unexpected output: {additional_output}")
                    return False
            
            # If export was successful, move the CSV file to downloadpath
            if return_code == 0 and downloadpath:
                row_count = self.move_exported_file(export_config, downloadpath)
                self.log_success(export_config, row_count)
            else:
                self.log_failure(export_config, stderr or "Unknown error")
            
            return return_code == 0
            
        except subprocess.TimeoutExpired:
            process.kill()
            print("Process timed out after 5 minutes")
            self.log_failure(export_config, "Process timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"Error running process: {e}")
            self.log_failure(export_config, f"Error running process: {e}")
            return False
    
    def process_ignore_columns(self, export_config, csv_file_path):
        """Rename columns specified in ignore_column parameter to ignore.columnname"""
        try:
            ignore_columns = export_config.get('ignore_column', [])
            
            if not ignore_columns:
                return  # No columns to ignore
            
            if not os.path.exists(csv_file_path):
                print(f"Warning: CSV file {csv_file_path} not found for column processing")
                return
            
            # Read the CSV file
            with open(csv_file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                print(f"Warning: CSV file {csv_file_path} is empty")
                return
            
            # Process header row
            header = rows[0]
            updated_header = []
            columns_renamed = []
            
            for col in header:
                if col in ignore_columns:
                    new_col_name = f"ignore.{col}"
                    updated_header.append(new_col_name)
                    columns_renamed.append(f"{col} -> {new_col_name}")
                else:
                    updated_header.append(col)
            
            if columns_renamed:
                # Update the header row
                rows[0] = updated_header
                
                # Write the updated CSV back
                with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                
                print(f"✓ Renamed columns: {', '.join(columns_renamed)}")
            else:
                print(f"ℹ️ No columns found to rename in {os.path.basename(csv_file_path)}")
                
        except Exception as e:
            print(f"Error processing ignore columns for {csv_file_path}: {e}")
    
    def move_exported_file(self, export_config, downloadpath):
        """Move the exported CSV file to the specified download path and return row count"""
        try:
            # Extract CSV filename from params
            params = export_config['params'].split()
            csv_filename = None
            
            # Find the CSV filename in the params
            for i, param in enumerate(params):
                if param == '-csv' and i + 1 < len(params):
                    csv_filename = params[i + 1]
                    break
            
            if not csv_filename:
                print("Warning: Could not find CSV filename in export parameters")
                return 0
            
            # Source file (script directory)
            source_file = os.path.join(self.script_dir, csv_filename)
            
            # Create destination directory if it doesn't exist
            os.makedirs(downloadpath, exist_ok=True)
            
            # Destination file
            dest_file = os.path.join(downloadpath, csv_filename)
            
            # Move the file if it exists and count rows
            if os.path.exists(source_file):
                # Count rows (excluding header)
                row_count = 0
                try:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        row_count = sum(1 for row in reader) - 1  # Subtract header row
                        row_count = max(0, row_count)  # Ensure non-negative
                except Exception as e:
                    print(f"Warning: Could not count rows in {csv_filename}: {e}")
                    row_count = 0
                
                shutil.move(source_file, dest_file)
                print(f"✓ Moved {csv_filename} to {downloadpath} ({row_count} rows)")
                
                # Process ignore columns after moving the file
                self.process_ignore_columns(export_config, dest_file)
                
                return row_count
            else:
                print(f"Warning: Export file {source_file} not found")
                return 0
                
        except Exception as e:
            print(f"Error moving exported file: {e}")
            return 0
    
    def log_success(self, export_config, row_count):
        """Log successful export to logs/success directory"""
        try:
            # Extract CSV filename and object name
            params = export_config['params'].split()
            csv_filename = None
            object_name = None
            
            for i, param in enumerate(params):
                if param == '-csv' and i + 1 < len(params):
                    csv_filename = params[i + 1]
                elif param == '-export' and i + 1 < len(params):
                    object_name = params[i + 1]
            
            if not csv_filename or not object_name:
                print("Warning: Could not extract filename or object name for success log")
                return
            
            # Create success log file path with run timestamp
            log_file = os.path.join(self.script_dir, 'logs', 'success', f'success_{self.run_timestamp}.csv')
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(log_file)
            
            # Write to log file
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow(['file_name', 'object_name', 'row_count', 'timestamp'])
                
                # Write success record
                writer.writerow([csv_filename, object_name, row_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                
        except Exception as e:
            print(f"Error logging success: {e}")
    
    def log_failure(self, export_config, failure_description):
        """Log failed export to logs/failure directory"""
        try:
            # Extract object name
            params = export_config['params'].split()
            object_name = None
            
            for i, param in enumerate(params):
                if param == '-export' and i + 1 < len(params):
                    object_name = params[i + 1]
                    break
            
            if not object_name:
                object_name = "Unknown"
            
            # Create failure log file path with run timestamp
            log_file = os.path.join(self.script_dir, 'logs', 'failure', f'failure_{self.run_timestamp}.csv')
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(log_file)
            
            # Write to log file
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow(['name', 'object_name', 'failure_description', 'timestamp'])
                
                # Write failure record
                writer.writerow([export_config['name'], object_name, failure_description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                
        except Exception as e:
            print(f"Error logging failure: {e}")
    
    def run_all_exports(self):
        """Execute all configured exports"""
        exports = self.config.get('exports', [])
        if not exports:
            print("No exports configured!")
            return
        
        print(f"🏁 Starting VaultLoader batch process with {len(exports)} exports")
        print(f"📅 Run timestamp: {self.run_timestamp}")
        print("-" * 80)
        
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        for i, export_config in enumerate(exports, 1):
            print(f"\n[{i}/{len(exports)}] Processing export: {export_config['name']}")
            
            # Check if export is active
            active = export_config.get('active', 1)
            if active == 0:
                print(f"⏭️ Skipping '{export_config['name']}' (inactive)")
                self.log_skipped(export_config)
                skipped_count += 1
                continue
            
            success = self.run_java_command(export_config)
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            print("-" * 40)
        
        # Print summary
        print(f"\n📊 Batch Export Summary:")
        print(f"✅ Successful exports: {success_count}")
        # List successful export files and line counts
        success_log = os.path.join(self.script_dir, 'logs', 'success', f'success_{self.run_timestamp}.csv')
        if os.path.exists(success_log):
            print("Exported files:")
            with open(success_log, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    file_name = row['file_name']
                    if file_name != 'SKIPPED' and file_name != '':
                        # Count lines in exported file (excluding header)
                        file_path = os.path.join(self.script_dir, file_name) if not os.path.isabs(file_name) else file_name
                        line_count = 0
                        try:
                            with open(file_path, 'r', encoding='utf-8') as expf:
                                line_count = sum(1 for _ in expf) - 1  # exclude header
                                if line_count < 0:
                                    line_count = 0
                        except Exception:
                            line_count = 'N/A'
                        print(f"- {file_name}: {line_count} lines")
        print(f"❌ Failed exports: {failure_count}")
        # List failed exports (object names)
        failure_log = os.path.join(self.script_dir, 'logs', 'failure', f'failure_{self.run_timestamp}.csv')
        if os.path.exists(failure_log):
            print("Failed objects:")
            with open(failure_log, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    object_name = row.get('object_name', '')
                    print(f"- {object_name}")
        print(f"⏭️ Skipped exports: {skipped_count}")
        print(f"📁 Log files created in logs/success/ and logs/failure/")
        print(f"🕒 Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    import csv
    import os
    import json
    from datetime import datetime

    def extract_veeva_object(params):
        """Extracts the object name after -export from params string."""
        if not params:
            return ""
        parts = params.split()
        if "-export" in parts:
            idx = parts.index("-export")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return ""

    def generate_report(config_path):
        """Generates and displays a report of the exports section."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        exports = config.get("exports", [])
        report_rows = []
        for export in exports:
            active = export.get("active", "")
            name = export.get("name", "")
            status = export.get("status", "")
            params = export.get("params", "")
            veeva_object = extract_veeva_object(params)
            columns = ",".join(export.get("columns", []))
            report_rows.append([active, name, status, veeva_object, columns])

        # Print table to stdout
        print("\nExport Configuration Report")
        print("-" * 80)
        header = ["active", "veeva_object", "status", "name"]
        print("{:<8} {:<50} {:<40} {:<50}".format(*header))
        print("-" * 148)
        for row in report_rows:
            active_display = row[0]
            if str(active_display) == "1":
                active_display = "\U0001F7E2"  # green circle
            elif str(active_display) == "0":
                active_display = "\u274C"  # red cross
            print("{:<8} {:<50} {:<40} {:<50}".format(active_display, row[3], row[2], row[1]))
        print("-" * 148)
        print("-" * 80)

        # Write CSV
        csv_filename = f"export_config_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(os.path.dirname(config_path), csv_filename)
        with open(csv_path, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["active", "name", "status", "veeva_object", "columns"])
            writer.writerows(report_rows)
        print(f"CSV report written to: {csv_path}\n")

    def main_menu():
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "vault_loader_config.json")
        while True:
            print("\nVault Loader Utility")
            print("1. Start Export")
            print("2. Export Configuration Report")
            print("3. Activate all object exports")
            print("4. Deactivate all object exports")
            print("0. Exit")
            choice = input("Select an option: ").strip()
            if choice == "1":
                runner = VaultLoaderRunner()
                runner.run_all_exports()
            elif choice == "2":
                generate_report(config_path)
            elif choice == "3":
                # Activate all exports
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                exports = config.get('exports', [])
                for export in exports:
                    export['active'] = 1
                # Backup
                backup_path = config_path + ".bak"
                import shutil
                shutil.copy2(config_path, backup_path)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                print(f"All exports activated. Backup saved as {backup_path}")
            elif choice == "4":
                # Deactivate all exports
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                exports = config.get('exports', [])
                for export in exports:
                    export['active'] = 0
                # Backup
                backup_path = config_path + ".bak"
                import shutil
                shutil.copy2(config_path, backup_path)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                print(f"All exports deactivated. Backup saved as {backup_path}")
            elif choice == "0":
                print("Exiting.")
                break
            else:
                print("Invalid option. Please try again.")

    main_menu()

if __name__ == "__main__":
    main()
