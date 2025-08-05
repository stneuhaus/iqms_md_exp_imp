# Vault Loader Automation

This directory contains an automated Python script for running Veeva VaultLoader exports with JSON-based configuration. The script is location-independent and can be run from anywhere on your system.

## Directory Structure

```
VaultLoader/
├── bin/                           # Executable files
│   └── VaultDataLoader.jar        # Veeva VaultLoader command line tool
├── config/                        # Configuration files
│   ├── vault_loader_config.json  # JSON configuration file
│   └── password.ini              # Password file
├── exports/                       # Export output directory
│   ├── *.csv                     # Exported CSV files (auto-moved here)
│   └── *.txt                     # Additional export files
├── logs/                          # Processing logs
│   ├── success/                  # Successful operation logs (CSV format)
│   │   └── success_YYYYMMDD_HHMMSS.csv  # Per-run success log files
│   ├── failure/                  # Failed operation logs (CSV format)
│   │   └── failure_YYYYMMDD_HHMMSS.csv  # Per-run failure log files
│   └── vl.log                    # General log file
├── start_vault_loader.py          # Main automation script
└── README.md                      # This documentation file
```

## Automation Overview

The `start_vault_loader.py` script automates multiple Veeva Vault exports using a JSON configuration file. It handles authentication, parameter building, and file management automatically.

### Key Features

- **Location Independent**: Run from any directory - no hardcoded paths
- **Batch Processing**: Execute multiple exports in sequence
- **Automatic File Management**: Move exported files to designated folder
- **Column Ignoring**: Rename specific columns to "ignore.columnname" format
- **Comprehensive Logging**: CSV logs for successful and failed exports
- **Flexible Column Selection**: Specify custom columns for each export
- **Progress Tracking**: Real-time feedback and summary reports
- **Error Handling**: Timeout management and detailed error reporting
- **Row Counting**: Automatic counting of exported data rows

## Configuration File: config/vault_loader_config.json

### General Section

The `general` section contains global settings used for all exports:

```json
{
    "general": {
        "java_exe": "c:\\jdk\\jdk-17.0.16.8-hotspot\\bin\\java.exe",
        "vault_loader": "bin\\VaultDataLoader.jar",
        "dns": "https://your-vault.veevavault.com",
        "username": "your.username@company.com",
        "password": "password.ini",
        "downloadpath": "exports"
    }
}
```

#### General Parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `java_exe` | Full path to Java executable | `c:\\jdk\\jdk-17.0.16.8-hotspot\\bin\\java.exe` |
| `vault_loader` | Path to VaultDataLoader.jar (relative to script) | `bin\\VaultDataLoader.jar` |
| `dns` | Veeva Vault DNS URL | `https://your-vault.veevavault.com` |
| `username` | Vault username | `your.username@company.com` |
| `password` | Password file path or direct password | `password.ini` or `your_password` |
| `downloadpath` | Directory for exported files (relative to script) | `exports` |

**Note**: All paths (vault_loader, downloadpath, password files) are resolved relative to the script location if they are not absolute paths. This makes the application location-independent.

#### Password Configuration:

The `password` parameter supports two modes:

1. **File-based (Recommended)**: Store password in a separate file
   ```json
   "password": "password.ini"
   ```
   Create a `config/password.ini` file containing only the password:
   ```
   your_actual_password
   ```

2. **Direct (Legacy)**: Store password directly in configuration
   ```json
   "password": "your_actual_password"
   ```

### Exports Section

The `exports` section contains an array of export configurations:

```json
{
    "exports": [
        {
            "name": "QMS_Unit_Export",
            "params": "-export qms_unit__c -csv qms_unit__c.csv",
            "columns": ["is_valid__c", "name__v", "state__v"],
            "ignore_column": ["internal_id__c", "temp_field__c"],
            "active": 1
        }
    ]
}
```

#### Export Parameters:

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `name` | Descriptive name for the export | Yes | `"QMS_Unit_Export"` |
| `params` | VaultLoader export parameters | Yes | `"-export qms_unit__c -csv file.csv"` |
| `columns` | Array of column names to export | No | `["name__v", "state__v"]` |
| `ignore_column` | Array of columns to rename to "ignore.columnname" | No | `["internal_id__c", "temp_field__c"]` |
| `active` | Enable/disable export (0=skip, 1=execute) | No | `1` |

**Note**: If `active` is not specified, the export defaults to active (1).

### Export Control

You can enable or disable individual exports using the `active` parameter:

```json
{
    "name": "QMS_Unit_Export",
    "params": "-export qms_unit__c -csv qms_unit__c.csv",
    "columns": ["name__v", "state__v"],
    "ignore_column": ["internal_id__c"],
    "active": 1  // 1 = execute, 0 = skip
}
```

### Column Ignore Functionality

The `ignore_column` parameter allows you to automatically rename specific columns in the exported CSV files:

```json
{
    "name": "QMS_Unit_Export",
    "params": "-export qms_unit__c -csv qms_unit__c.csv",
    "columns": ["name__v", "state__v", "internal_id__c", "temp_field__c"],
    "ignore_column": ["internal_id__c", "temp_field__c"]
}
```

**How it works**:
- After the CSV file is exported and moved to the download directory
- Columns specified in `ignore_column` are renamed to `ignore.columnname`
- Example: `internal_id__c` becomes `ignore.internal_id__c`
- This helps identify columns that should be ignored in downstream processing
- Empty arrays `[]` are valid and result in no column renaming

**Benefits**:
- **Data Processing**: Mark columns to ignore without removing data
- **Downstream Integration**: Clear indication of columns to skip
- **Flexible Configuration**: Per-export column ignore settings
- **Data Preservation**: Original data is retained but clearly marked

**Benefits**:
- **Selective Execution**: Run only specific exports without modifying the configuration
- **Testing**: Disable problematic exports during troubleshooting
- **Maintenance**: Keep configurations for future use without deleting them
- **Staging**: Different active settings for different environments

**Skipped Export Logging**:
- Skipped exports are logged in the success log file
- Marked with `SKIPPED` in the file_name column
- Row count shows `N/A`
- Helps track which exports were intentionally disabled

## Usage Instructions

### 1. Configure Settings

Edit `config/vault_loader_config.json` with your specific settings:

1. **Update DNS**: Replace with your Vault URL
2. **Set Credentials**: Update username and password file reference
3. **Configure Exports**: Add/modify export definitions
4. **Set Download Path**: Specify where files should be saved

Create or update `config/password.ini` with your vault password.

### 2. Run Exports

Execute the automation script from any directory:

```bash
# The script is now location-independent
cd /path/to/your/vault-loader-project
python start_vault_loader.py

# Or run from anywhere if Python path is configured
python /full/path/to/start_vault_loader.py
```

**Location Independence**: The script automatically detects its location and resolves all relative paths accordingly. No need to change to a specific working directory.

### 3. Monitor Progress

The script provides real-time feedback and automatic logging:

```
============================================================
Running export: QMS_Unit_Export
Parameters: -export qms_unit__c -csv qms_unit__c.csv
DNS: https://your-vault.veevavault.com
Download path: exports
Columns: is_valid__c name__v state__v
Ignore columns: internal_id__c temp_field__c
============================================================
🚀 Starting Java process for: QMS_Unit_Export
Command: java.exe -jar bin\VaultDataLoader.jar -dns https://your-vault.veevavault.com -u username -p [HIDDEN] -export qms_unit__c -csv qms_unit__c.csv -downloadpath exports -columns is_valid__c,name__v,state__v
✓ Export 'QMS_Unit_Export' completed successfully
✓ Moved qms_unit__c.csv to exports (1247 rows)
✓ Renamed columns: internal_id__c -> ignore.internal_id__c, temp_field__c -> ignore.temp_field__c
```

**Automatic Logging**:
- Success logs: `logs/success/success_20250801.csv`
- Failure logs: `logs/failure/failure_20250801.csv`
- Daily log files with detailed export information

## Command Structure

The script builds VaultLoader commands in this order:

1. **Connection**: `-dns <vault_url>`
2. **Authentication**: `-u <username> -p <password>`
3. **Export Definition**: `-export <object> -csv <filename>`
4. **Download Path**: `-downloadpath <folder>`
5. **Column Selection**: `-columns <col1,col2,col3>`

Final command example:
```bash
java.exe -jar bin\VaultDataLoader.jar -dns https://vault.com -u user -p pass -export qms_unit__c -csv file.csv -downloadpath exports -columns name__v,state__v
```

## File Management

- **Input**: CSV parameters defined in configuration
- **Processing**: VaultLoader creates files in working directory
- **Output**: Files automatically moved to `downloadpath` folder
- **Column Processing**: Columns in `ignore_column` arrays are renamed to `ignore.columnname`
- **Organization**: All exports centralized in designated folder
- **Success Logging**: Each successful export logged to `logs/success/success_YYYYMMDD_HHMMSS.csv`
- **Failure Logging**: Each failed export logged to `logs/failure/failure_YYYYMMDD_HHMMSS.csv`
- **Location Independence**: All paths resolved relative to script location

### Success Log Format (logs/success/success_YYYYMMDD_HHMMSS.csv)

| Column | Description | Example |
|--------|-------------|---------|
| `file_name` | Name of exported CSV file or "SKIPPED" | `qms_unit__c.csv` or `SKIPPED` |
| `object_name` | Veeva object name | `qms_unit__c` |
| `row_count` | Number of data rows (excluding header) or "N/A" | `1247` or `N/A` |
| `timestamp` | When the export completed | `2025-08-01 14:30:25` |

**Example Success Log**:
```csv
file_name,object_name,row_count,timestamp
10_qms_unit__c.csv,qms_unit__c,1247,2025-08-01 14:30:25
SKIPPED,registration_name__c,N/A,2025-08-01 14:30:26
07_country__v.csv,country__v,195,2025-08-01 14:32:10
```

### Failure Log Format (logs/failure/failure_YYYYMMDD_HHMMSS.csv)

| Column | Description | Example |
|--------|-------------|---------|
| `name` | Export configuration name | `QMS_Unit_Export` |
| `object_name` | Vault object type attempted | `qms_unit__c` |
| `failure_description` | Error description | `Authentication failed` |
| `timestamp` | Failure time | `2025-08-01 14:30:25` |

## Error Handling

- **Timeouts**: 5-minute timeout per export
- **File Operations**: Graceful handling of missing files
- **Process Errors**: Detailed error messages and return codes
- **Summary Reports**: Success/failure counts for batch operations

## Security Considerations

- **Password Storage**: Two options available:
  - **File-based (Recommended)**: Store password in separate `config/password.ini` file
  - **Direct**: Store password directly in JSON configuration (less secure)
- **File Permissions**: Ensure configuration and password files have appropriate access controls
- **Password File**: Keep `config/password.ini` out of version control systems
- **Configuration Organization**: All sensitive files stored in `config/` directory
- **Backup**: Consider backing up configuration (without credentials)

## Troubleshooting

### Common Issues:

1. **Java Path**: Ensure Java executable path is correct
2. **JAR Location**: Verify VaultDataLoader.jar is in bin/ directory
3. **DNS URL**: Check Vault DNS URL is accessible
4. **Credentials**: Verify username/password are correct
5. **Permissions**: Ensure write access to export directory

### Log Analysis:

- Check console output for detailed error messages
- Review VaultLoader output for authentication issues
- Verify file creation in working directory before move operation
- **Success Logs**: Review daily success logs for export statistics and row counts
- **Failure Logs**: Analyze failure logs for patterns and recurring issues
- **Log Location**: All logs stored in `logs/success/` and `logs/failure/` directories

### Console Output

### Export Processing Messages

- **🚀 Active Export**: `Starting Java process for: QMS_Unit_Export`
- **⏭️ Skipped Export**: `Skipping 'registration_name__c' (inactive)`
- **✅ Success**: `Export 'QMS_Unit_Export' completed successfully`
- **✓ Column Renaming**: `Renamed columns: internal_id__c -> ignore.internal_id__c`
- **ℹ️ No Columns to Rename**: `No columns found to rename in qms_unit__c.csv`
- **❌ Failure**: `Export 'QMS_Unit_Export' failed with return code 1`

### Summary Report

```
📊 Batch Export Summary:
✅ Successful exports: 7
❌ Failed exports: 1
⏭️ Skipped exports: 2
📁 Log files created in logs/success/ and logs/failure/
🕒 Run completed at: 2025-08-01 14:35:22
```

### archives/
- Move processed input files here to maintain a record
- Helps prevent accidental reprocessing
- Consider periodic cleanup based on retention policies

## Best Practices

1. **Location Independence**: Take advantage of the location-independent design - copy the entire project folder anywhere
2. **Backup**: Regularly backup configuration and important data files
3. **Column Management**: Use `ignore_column` to mark columns for downstream processing exclusion
4. **Naming**: Use consistent naming conventions with timestamps
5. **Security**: Protect configuration files containing credentials
6. **Cleanup**: Implement regular cleanup procedures for logs and archives
7. **Monitoring**: Review logs regularly for operational insights
8. **Testing**: Use `active: 0` to disable exports during testing without removing configuration

## Installation and Deployment

### Quick Deployment
1. Copy the entire project folder to any location on your system
2. Place `VaultDataLoader.jar` in the `bin/` directory
3. Update `config/vault_loader_config.json` with your settings
4. Create `config/password.ini` with your password
5. Run `python start_vault_loader.py` from anywhere

### No Installation Required
- No hardcoded paths to update
- No environment variables to set
- Works from any directory location
- Portable across different systems

## Quick Start

1. **Deploy**: Copy the project folder to any location
2. **Configure**: Update `config/vault_loader_config.json` with your settings
3. **Credentials**: Create `config/password.ini` with your password
4. **JAR File**: Place `VaultDataLoader.jar` in the `bin/` directory  
5. **Run**: Execute `python start_vault_loader.py` from the project directory
6. **Monitor**: Check `logs/` for results and `exports/` for CSV files

**Location Flexibility**: The application automatically adapts to its location - no path configuration needed!
