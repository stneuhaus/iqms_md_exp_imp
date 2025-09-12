import subprocess
import sys
import os
import json
import shutil
import csv
from datetime import datetime

class VaultImportRunner:
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
    
    def log_skipped(self, import_config):
        """Log skipped import to success log"""
        success_log = os.path.join(self.script_dir, 'logs', 'success', f'success_{self.run_timestamp}.csv')
        
        # Extract object name from params
        params = import_config['params'].split()
        object_name = ""
        if '-import' in params:
            import_index = params.index('-import')
            if import_index + 1 < len(params):
                object_name = params[import_index + 1]
        
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
    
    def run_java_command(self, import_config):
        """Execute the Java VaultLoader with given import parameters"""
        
        # Check if import is active
        active = import_config.get('active', 1)  # Default to 1 (active) if not specified
        if active == 0:
            print(f"⏭️ Skipping '{import_config['name']}' (inactive)")
            self.log_skipped(import_config)
            return True  # Return True to indicate successful skip
        
        # Get general configuration
        general = self.config['general']
        import_settings = self.config.get('import_settings', {})
        java_exe = general['java_exe']
        vault_loader_path = general['vault_loader']
        # Make vault_loader path absolute if it's relative
        if not os.path.isabs(vault_loader_path):
            vault_loader = os.path.join(self.script_dir, vault_loader_path)
        else:
            vault_loader = vault_loader_path
        dns = import_settings.get('dns', '')
        username = import_settings.get('username', '')
        password_param = import_settings.get('password', '')
        password = self.load_password(password_param)
        
        # Build Java command with dns, username and password parameters
        java_command = [java_exe, '-jar', vault_loader]
        
        # Add DNS parameter if present
        if dns:
            java_command.extend(['-dns', dns])
        
        # Add username and password
        java_command.extend(['-u', username, '-p', password])
        
        # Add import parameters
        params_str = import_config['params']
        import_path = import_config.get('import_path', None)
        import_path_full = None
        if import_path:
            if not os.path.isabs(import_path):
                import_path_full = os.path.abspath(os.path.join(self.script_dir, import_path))
            else:
                import_path_full = import_path
            # Replace [import_path] placeholder
            if '[import_path]' in params_str:
                params_str = params_str.replace('[import_path]', import_path_full)
        params = params_str.split()
        java_command.extend(params)
        
        print(f"🚀 Starting Java process for: {import_config['name']}")
        # Build display command (hide password)
        display_params = params.copy()
        dns_display = f"-dns {dns} " if dns else ""
        command_display = f"{java_exe} -jar {vault_loader} {dns_display}-u {username} -p [HIDDEN] {' '.join(display_params)}"
        print(f"Command: {command_display}")
        if import_path_full:
            print(f"Used file for import: {import_path_full}")
        
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
            # Get timeout from import_settings (default 1800 seconds)
            import_settings = self.config.get('import_settings', {})
            timeout_val = import_settings.get('time_out', 1800)
            stdout, stderr = process.communicate(timeout=timeout_val)
            print("Output:")
            print(stdout)
            if stderr:
                print("Errors:")
                print(stderr)
            return_code = process.returncode
            print(f"Process completed with return code: {return_code}")
            # Check if stdout contains more than the standard header
            expected_header = "Vault Loader. (c)Veeva Systems 2014-2021. All rights reserved."
            error_detected = False
            if stdout and stdout.strip() != expected_header:
                additional_output = stdout.strip()
                if additional_output.startswith(expected_header):
                    remaining_output = additional_output[len(expected_header):].strip()
                    if remaining_output:
                        print(f"Warning: Additional output detected: {remaining_output}")
                        self.log_failure(import_config, f"Additional output: {remaining_output}")
                        error_detected = True
                elif additional_output != expected_header:
                    print(f"Warning: Unexpected output: {additional_output}")
                    self.log_failure(import_config, f"Unexpected output: {additional_output}")
                    error_detected = True
            # If import was successful, log it
            if return_code == 0 and not error_detected:
                self.log_success(import_config)
            else:
                self.log_failure(import_config, stderr or "Unknown error")
            # --- Post-import file management ---
            # Prepare destination folder name from DNS
            import_settings = self.config.get('import_settings', {})
            dns = import_settings.get('dns', '')
            dns_folder = dns.replace('https://', '').replace('/', '_')
            dest_folder = os.path.join(self.script_dir, 'imports', dns_folder)
            os.makedirs(dest_folder, exist_ok=True)
            # Copy imported CSV file
            if import_path_full and os.path.exists(import_path_full):
                shutil.copy2(import_path_full, dest_folder)
                print(f"Copied imported file to {dest_folder}")
            # Move and rename Java log file if present
            # Find log file in working directory matching *_FAILURE.csv or *_SUCCESS.csv
            log_candidates = [f for f in os.listdir(self.script_dir) if f.upper().endswith('_FAILURE.CSV') or f.upper().endswith('_SUCCESS.CSV')]
            for log_file in log_candidates:
                log_path = os.path.join(self.script_dir, log_file)
                # Determine new log file name: use import file name (without extension) + STATUS
                status = '_FAILURE.csv' if log_file.upper().endswith('_FAILURE.CSV') else '_SUCCESS.csv'
                import_base = os.path.splitext(os.path.basename(import_path_full))[0] if import_path_full else 'import'
                new_log_name = import_base + status
                new_log_path = os.path.join(dest_folder, new_log_name)
                shutil.move(log_path, new_log_path)
                # Print file path in blue
                BLUE = '\033[94m'
                RESET = '\033[0m'
                print(f"Moved and renamed log file to: {BLUE}{new_log_path}{RESET}")
            return return_code == 0 and not error_detected
        except subprocess.TimeoutExpired:
            process.kill()
            print("Process timed out after 5 minutes")
            self.log_failure(import_config, "Process timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"Error running process: {e}")
            self.log_failure(import_config, f"Error running process: {e}")
            return False
    
    def log_success(self, import_config):
        """Log successful import to logs/success directory"""
        try:
            # Extract CSV filename and object name
            # Use resolved params for logging
            params_str = import_config['params']
            import_path = import_config.get('import_path', None)
            import_path_full = None
            if import_path:
                if not os.path.isabs(import_path):
                    import_path_full = os.path.abspath(os.path.join(self.script_dir, import_path))
                else:
                    import_path_full = import_path
                if '[import_path]' in params_str:
                    params_str = params_str.replace('[import_path]', import_path_full)
            params = params_str.split()
            csv_filename = None
            object_name = None
            for i, param in enumerate(params):
                if param == '-csv' and i + 1 < len(params):
                    csv_filename = params[i + 1]
                elif param == '-import' and i + 1 < len(params):
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
                writer.writerow([csv_filename, object_name, 'N/A', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                
        except Exception as e:
            print(f"Error logging success: {e}")
    
    def log_failure(self, import_config, failure_description):
        """Log failed import to logs/failure directory"""
        try:
            # Extract object name
            params = import_config['params'].split()
            object_name = None
            
            for i, param in enumerate(params):
                if param == '-import' and i + 1 < len(params):
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
                writer.writerow([import_config['name'], object_name, failure_description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                
        except Exception as e:
            print(f"Error logging failure: {e}")
    
    def run_all_imports(self):
        """Execute all configured imports"""
        imports = self.config.get('imports', [])
        if not imports:
            print("No imports configured!")
            return
        
        print(f"🏁 Starting VaultLoader batch import process with {len(imports)} imports")
        print(f"📅 Run timestamp: {self.run_timestamp}")
        print("-" * 80)
        
        success_count = 0
        failure_count = 0
        skipped_count = 0
        success_files_list = []
        failure_files_list = []

        for i, import_config in enumerate(imports, 1):
            print(f"\n[{i}/{len(imports)}] Processing import: {import_config['name']}")
            # Check if import is active
            active = import_config.get('active', 1)
            if active == 0:
                print(f"⏭️ Skipping '{import_config['name']}' (inactive)")
                self.log_skipped(import_config)
                skipped_count += 1
                continue
            success = self.run_java_command(import_config)
            # Determine loader file (imported CSV) for this import
            loader_file = import_config.get('import_path') or import_config.get('file') or import_config.get('import_file') or import_config.get('name')
            # If run_java_command returns False, check for log files to determine real status
            import_settings = self.config.get('import_settings', {})
            dns = import_settings.get('dns', '').replace('https://', '').replace('/', '_')
            dest_folder = os.path.join(self.script_dir, 'imports', dns)
            failure_files = []
            success_files = []
            if os.path.isdir(dest_folder):
                for f in os.listdir(dest_folder):
                    if f.endswith('_FAILURE.csv'):
                        failure_files.append(f)
                    elif f.endswith('_SUCCESS.csv'):
                        success_files.append(f)
            # Try to match the log file to the loader file for this import
            matched_success = None
            matched_failure = None
            if loader_file:
                loader_base = os.path.splitext(os.path.basename(loader_file))[0]
                for f in success_files:
                    if loader_base in f:
                        matched_success = os.path.join(dest_folder, f)
                        break
                for f in failure_files:
                    if loader_base in f:
                        matched_failure = os.path.join(dest_folder, f)
                        break
            # Decide result for this import
            if matched_failure:
                print("Failure file detected:")
                print("-", matched_failure)
                failure_files_list.append(matched_failure)
                while True:
                    proceed = input("Proceed with next import? (y/n): ").strip().lower()
                    if proceed == 'y':
                        break
                    elif proceed == 'n':
                        print("Aborted by user.")
                        return
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")
                failure_count += 1
            elif matched_success:
                print("Success file detected (no failure file): Import counted as successful.")
                print("-", matched_success)
                success_files_list.append(matched_success)
                success_count += 1
            else:
                print("No failure or success file detected: Import counted as failed.")
                if loader_file:
                    failure_files_list.append(loader_file)
                failure_count += 1
            print("-" * 40)

        # Print summary
        print(f"\n📊 Batch Import Summary:")
        print(f"✅ Successful imports: {success_count}")
        if success_files_list:
            print("   Loader files counted as successful:")
            for f in success_files_list:
                print(f"   - {f}")
        print(f"❌ Failed imports: {failure_count}")
        if failure_files_list:
            print("   Loader files counted as failed:")
            for f in failure_files_list:
                print(f"   - {f}")
        print(f"⏭️ Skipped imports: {skipped_count}")
        print(f"📁 Log files created in logs/success/ and logs/failure/")
        print(f"🕒 Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
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

if __name__ == "__main__":
    main()
