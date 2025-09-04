# Vault Export/Import Loader Automation

This directory contains automated Python scripts for running Veeva VaultLoader exports and imports with JSON-based configuration. The scripts are location-independent and can be run from anywhere on your system.

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
├── input/                         # Import source directory
│   ├── *.csv                     # CSV files for import operations
│   └── *.txt                     # Additional import files
├── logs/                          # Processing logs
│   ├── success/                  # Successful operation logs (CSV format)
│   │   └── success_YYYYMMDD_HHMMSS.csv  # Per-run success log files
│   ├── failure/                  # Failed operation logs (CSV format)
│   │   └── failure_YYYYMMDD_HHMMSS.csv  # Per-run failure log files
│   └── vl.log                    # General log file
├── start_export_vault_loader.py   # Export automation script
├── start_import_vault_loader.py   # Import automation script
└── README.md                      # This documentation file
```

## Automation Overview

The `start_export_vault_loader.py` script automates multiple Veeva Vault exports and the `start_import_vault_loader.py` script automates multiple Veeva Vault imports using a shared JSON configuration file. Both scripts handle authentication, parameter building, and file management automatically.

### Key Features

- **Location Independent**: Run from any directory - no hardcoded paths
- **Dual Operations**: Separate scripts for exports and imports
- **Batch Processing**: Execute multiple exports or imports in sequence
- **WHERE Clause Filtering**: Filter export records at source using Veeva query syntax
- **Automatic File Management**: Move exported files to designated folder
- **Column Ignoring**: Rename specific columns to "ignore.columnname" format (exports only)
- **Comprehensive Logging**: CSV logs for successful and failed operations
- **Flexible Column Selection**: Specify custom columns for each export
- **Progress Tracking**: Real-time feedback and summary reports
- **Error Handling**: Timeout management and detailed error reporting
- **Row Counting**: Automatic counting of exported data rows
- **Shared Configuration**: Both scripts use the same configuration file

## Configuration File: config/vault_loader_config.json


### Configuration Structure

The configuration file now separates connection credentials for exports and imports:

```json
{
    "general": {
        "java_exe": "c:\jdk\jdk-17.0.16.8-hotspot\bin\java.exe",
        "vault_loader": "bin\VaultDataLoader.jar",
        "downloadpath": "exports"
    },
    "export_settings": {
        "dns": "https://your-vault.veevavault.com",
        "username": "your.username@company.com",
        "password": "password.ini"
    },
    "import_settings": {
        "dns": "https://your-vault.veevavault.com",
        "username": "your.username@company.com",
        "password": "password.ini"
    },
    ...
}
```

#### General Parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `java_exe` | Full path to Java executable | `c:\jdk\jdk-17.0.16.8-hotspot\bin\java.exe` |
| `vault_loader` | Path to VaultDataLoader.jar (relative to script) | `bin\VaultDataLoader.jar` |
| `downloadpath` | Directory for exported files (relative to script) | `exports` |

#### Export/Import Settings Parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `dns` | Veeva Vault DNS URL | `https://your-vault.veevavault.com` |
| `username` | Vault username | `your.username@company.com` |
| `password` | Password file path or direct password | `password.ini` or `your_password` |

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
            "where": "state__v='active__v'",
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
| `where` | WHERE clause for filtering records | No | `"state__v='active__v'"` |
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
    "where": "state__v='active__v'",
    "columns": ["name__v", "state__v"],
    "ignore_column": ["internal_id__c"],
    "active": 1  // 1 = execute, 0 = skip
}
```

### WHERE Clause Filtering

The `where` parameter allows you to filter records during export using Veeva Vault query syntax:

```json
{
    "name": "Active_QMS_Units",
    "params": "-export qms_unit__c -csv active_qms_units.csv",
    "where": "state__v='active__v' AND is_valid__c=true",
    "columns": ["name__v", "state__v", "is_valid__c"]
}
```

**Common WHERE clause examples**:
- **State filtering**: `"state__v='active__v'"`
- **Date ranges**: `"created_date__v >= '2024-01-01'"`
- **Multiple conditions**: `"state__v='active__v' AND is_valid__c=true"`
- **Text matching**: `"name__v CONTAINS 'test'"`
- **Null checks**: `"description__c IS NOT NULL"`

**Benefits**:
- **Performance**: Reduce export size by filtering at source
- **Relevance**: Export only records that meet specific criteria
- **Efficiency**: Avoid processing unwanted records
- **Flexibility**: Different filters for different environments

**Note**: Leave `where` as an empty string `""` if no filtering is needed.

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

### Imports Section


The `imports` section contains an array of import configurations for the `start_import_vault_loader.py` script. Each import can specify an `import_path` for the file to be imported:

```json
{
    "imports": [
        {
            "name": "QMS_Unit_Import",
            "params": "-import qms_unit__c -csv qms_unit_import.csv",
            "import_path": "input/qms_unit_import.csv",
            "active": 1
        }
    ]
}
```

#### Import Parameters:

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `name` | Descriptive name for the import | Yes | `"QMS_Unit_Import"` |
| `params` | VaultLoader import parameters. Use `[import_path]` as a placeholder to reference the file specified in `import_path`. | Yes | `"-import qms_unit__c -csv [import_path]"` |
| `import_path` | Relative path to the file to be imported | Yes | `"input/qms_unit_import.csv"` |
| `active` | Enable/disable import (0=skip, 1=execute) | No | `1` |

**Note**: If the `params` value contains `[import_path]`, it will be automatically replaced with the full path specified in the `import_path` parameter. The log file will record which file was used for each import job.

### Post-Import File Management

After each import:
- A folder is created under `imports/` named after the Vault DNS (from `import_settings`), with `https://` removed.
- The imported CSV file is copied to this folder.
- If the Java program creates a log file (ending with `_FAILURE.csv` or `_SUCCESS.csv`), it is moved to this folder and renamed to match the import file name (except for the STATUS part).

**Example:**
- DNS: `https://your-vault.veevavault.com` → Folder: `imports/your-vault.veevavault.com`
- Imported file: `input/qms_unit_import.csv` → Copied to `imports/your-vault.veevavault.com/qms_unit_import.csv`
- Java log file: `xxxxxxx_yyyyyyy_create-qms_unit__c_2025-08-22_14_30_00_SUCCESS.csv` → Moved and renamed to `imports/your-vault.veevavault.com/qms_unit_import_SUCCESS.csv`

### Import Control

Similar to exports, you can enable or disable individual imports:

```json
{
    "name": "QMS_Unit_Import",
    "params": "-import qms_unit__c -csv qms_unit_import.csv",
    "active": 1  // 1 = execute, 0 = skip
}
```

**Import Benefits**:
- **Batch Processing**: Execute multiple imports in sequence
- **Selective Execution**: Run only specific imports without modifying configuration
- **Error Handling**: Comprehensive logging and error reporting
- **Shared Configuration**: Uses the same general settings as exports

## Usage Instructions

### 1. Configure Settings

Edit `config/vault_loader_config.json` with your specific settings:

1. **Update DNS**: Replace with your Vault URL
2. **Set Credentials**: Update username and password file reference
3. **Configure Exports**: Add/modify export definitions in the `exports` section
4. **Configure Imports**: Add/modify import definitions in the `imports` section
5. **Set Download Path**: Specify where exported files should be saved

Create or update `config/password.ini` with your vault password.

### 2. Run Operations

Execute the automation scripts from any directory:

**For Exports:**
```bash
# The scripts are now location-independent
cd /path/to/your/vault-loader-project
python start_export_vault_loader.py

# Or run from anywhere if Python path is configured
python /full/path/to/start_export_vault_loader.py
```

**For Imports:**
```bash
cd /path/to/your/vault-loader-project
python start_import_vault_loader.py

# Or run from anywhere if Python path is configured
python /full/path/to/start_import_vault_loader.py
```

**Location Independence**: The scripts automatically detect their location and resolve all relative paths accordingly. No need to change to a specific working directory.

### 3. Monitor Progress

The scripts provide real-time feedback and automatic logging:

**Export Example:**
```
============================================================
Running export: QMS_Unit_Export
Parameters: -export qms_unit__c -csv qms_unit__c.csv
DNS: https://your-vault.veevavault.com
Download path: exports
Where clause: state__v='active__v'
Columns: is_valid__c name__v state__v
Ignore columns: internal_id__c temp_field__c
============================================================
🚀 Starting Java process for: QMS_Unit_Export
Command: java.exe -jar bin\VaultDataLoader.jar -dns https://your-vault.veevavault.com -u username -p [HIDDEN] -export qms_unit__c -csv qms_unit__c.csv -where state__v='active__v' -downloadpath exports -columns is_valid__c,name__v,state__v
✓ Export 'QMS_Unit_Export' completed successfully
✓ Moved qms_unit__c.csv to exports (1247 rows)
✓ Renamed columns: internal_id__c -> ignore.internal_id__c, temp_field__c -> ignore.temp_field__c
```

**Import Example:**
```
============================================================
Running import: QMS_Unit_Import
Parameters: -import qms_unit__c -csv qms_unit_import.csv
DNS: https://your-vault.veevavault.com
============================================================
🚀 Starting Java process for: QMS_Unit_Import
Command: java.exe -jar bin\VaultDataLoader.jar -dns https://your-vault.veevavault.com -u username -p [HIDDEN] -import qms_unit__c -csv qms_unit_import.csv
✓ Import 'QMS_Unit_Import' completed successfully
```

**Automatic Logging**:
- Success logs: `logs/success/success_20250801.csv`
- Failure logs: `logs/failure/failure_20250801.csv`
- Daily log files with detailed export information

## Command Structure

### Export Commands

The export script builds VaultLoader commands in this order:

1. **Connection**: `-dns <vault_url>`
2. **Authentication**: `-u <username> -p <password>`
3. **Export Definition**: `-export <object> -csv <filename>`
4. **WHERE Clause**: `-where <filter_conditions>` (if specified)
5. **Download Path**: `-downloadpath <folder>`
6. **Column Selection**: `-columns <col1,col2,col3>`

Export command example:
```bash
java.exe -jar bin\VaultDataLoader.jar -dns https://vault.com -u user -p pass -export qms_unit__c -csv file.csv -where "state__v='active__v'" -downloadpath exports -columns name__v,state__v
```

### Import Commands

The import script builds VaultLoader commands in this order:

1. **Connection**: `-dns <vault_url>`
2. **Authentication**: `-u <username> -p <password>`
3. **Import Definition**: `-import <object> -csv <filename>`

Import command example:
```bash
java.exe -jar bin\VaultDataLoader.jar -dns https://vault.com -u user -p pass -import qms_unit__c -csv import_file.csv
```

## File Management

### Export Operations
- **Input**: Export parameters defined in configuration
- **Processing**: VaultLoader creates files in working directory
- **Output**: Files automatically moved to `downloadpath` folder
- **Column Processing**: Columns in `ignore_column` arrays are renamed to `ignore.columnname`
- **Organization**: All exports centralized in designated folder

### Import Operations
- **Input**: CSV files must be present in working directory or specified path
- **Processing**: VaultLoader reads CSV files and imports data to Vault
- **Requirements**: Import CSV files must match Vault object structure

### Common Features
- **Success Logging**: Each successful operation logged to `logs/success/success_YYYYMMDD_HHMMSS.csv`
- **Failure Logging**: Each failed operation logged to `logs/failure/failure_YYYYMMDD_HHMMSS.csv`
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
5. Run `python start_export_vault_loader.py` from anywhere

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
5. **Run**: Execute `python start_export_vault_loader.py` from the project directory
     - You will see an option menu:
         ```
         Vault Loader Utility
         1. Start Export
         2. Export Configuration Report
         0. Exit
         Select an option:
         ```
     - **Option 1:** Runs the export process as before.
     - **Option 2:** Generates a report of the current export configuration.
         - The report is shown as a table in the console.
         - A CSV file is also created in the `config` folder, with columns:
             `active`, `name`, `status`, `veeva_object`, `columns`
         - `veeva_object` is extracted from the `params` field (the value after `-export`).

         Example table output:
         ```
         active    name                                    status                        veeva_object
         -----------------------------------------------------------------------------------------------
         1         05_specification_id__c                  all attributes included       specification_id__c
         1         11_registration_name__c                 all attributes included       registration_name__c
         ...
         ```

         Example CSV output:
         ```
         active,name,status,veeva_object,columns
         1,05_specification_id__c,all attributes included,specification_id__c,id,name__v,description__c,...
         ...
         ```
6. **Monitor**: Check `logs/` for results and `exports/` for CSV files

**Location Flexibility**: The application automatically adapts to its location - no path configuration needed!
