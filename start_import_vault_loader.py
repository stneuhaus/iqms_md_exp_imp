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
        params = import_config['params'].split()
        java_command.extend(params)
        
        print(f"🚀 Starting Java process for: {import_config['name']}")
        # Build display command (hide password)
        display_params = params.copy()
        
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
            stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
            
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
                        self.log_failure(import_config, f"Additional output: {remaining_output}")
                        return False
                elif additional_output != expected_header:
                    # Completely different output
                    print(f"Warning: Unexpected output: {additional_output}")
                    self.log_failure(import_config, f"Unexpected output: {additional_output}")
                    return False
            
            # If import was successful, log it
            if return_code == 0:
                self.log_success(import_config)
            else:
                self.log_failure(import_config, stderr or "Unknown error")
            
            return return_code == 0
            
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
            params = import_config['params'].split()
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
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            print("-" * 40)
        
        # Print summary
        print(f"\n📊 Batch Import Summary:")
        print(f"✅ Successful imports: {success_count}")
        print(f"❌ Failed imports: {failure_count}")
        print(f"⏭️ Skipped imports: {skipped_count}")
        print(f"📁 Log files created in logs/success/ and logs/failure/")
        print(f"🕒 Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    # Create VaultImport runner
    runner = VaultImportRunner()
    
    # Run all configured imports
    runner.run_all_imports()

if __name__ == "__main__":
    main()
