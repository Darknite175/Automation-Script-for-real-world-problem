# Automated Report Generation & Distribution System

## Problem Statement

Organizations often need to:
- Generate periodic reports from data sources
- Organize reports with timestamps
- Distribute reports via email to stakeholders
- Log all activities for audit purposes
- Handle errors gracefully without manual intervention

**Current Challenge:** Manual report generation and email distribution is time-consuming and error-prone, occurring multiple times per week across teams.

## Solution Overview

This automation tool provides:
1. ✅ Automated CSV/data report generation
2. ✅ File organization by date and category
3. ✅ Email distribution to multiple recipients
4. ✅ Comprehensive logging and error handling
5. ✅ Command-line configuration
6. ✅ Scheduling capability (via cron/Task Scheduler)
7. ✅ Email/console notifications
8. ✅ Extensive testing suite

## Architecture

```
automation-tool/
├── report_generator.py      # Main automation script
├── config.yaml             # Configuration file
├── requirements.txt        # Dependencies
├── logs/                   # Log files directory
├── reports/                # Generated reports directory
├── tests/                  # Test suite
│   ├── test_generator.py
│   ├── sample_data.csv
│   └── test_config.yaml
└── README.md
```

## Features

### Core Functionality
- **Data Processing**: Reads source data and generates formatted reports
- **File Management**: Organizes reports with timestamps and categories
- **Email Distribution**: Sends reports to configured recipients
- **Error Handling**: Graceful error management with detailed logging
- **Configuration**: YAML-based config for easy customization

### Advanced Features
- **Command-line Arguments**: Override config via CLI
- **Scheduling**: Compatible with cron (Linux) and Task Scheduler (Windows)
- **Notifications**: Email and console notifications
- **Logging**: Detailed execution logs with timestamps
- **Testing**: Comprehensive test scenarios

## Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd automation-script

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `config.yaml`:
```yaml
email:
  sender: your-email@gmail.com
  smtp_server: smtp.gmail.com
  smtp_port: 587
  password: your-app-password

recipients:
  - stakeholder1@company.com
  - stakeholder2@company.com

data_source:
  path: ./data/source.csv
  encoding: utf-8

report:
  output_dir: ./reports
  format: csv
  include_summary: true

logging:
  level: INFO
  file: ./logs/automation.log
```

### Basic Usage

```bash
# Run with default config
python report_generator.py

# Run with custom config
python report_generator.py --config custom_config.yaml

# Run specific report type
python report_generator.py --report-type sales

# Disable email notifications (dry run)
python report_generator.py --no-email

# Verbose logging
python report_generator.py --verbose
```

### Schedule Execution

**Linux/macOS (Cron):**
```bash
# Edit crontab
crontab -e

# Add entry to run daily at 8 AM
0 8 * * * cd /path/to/automation-script && python report_generator.py >> logs/cron.log 2>&1
```

**Windows (Task Scheduler):**
```batch
# Create scheduled task
schtasks /create /tn "AutomationReport" /tr "python C:\path\to\report_generator.py" /sc DAILY /st 08:00
```

## Results

See `DEMONSTRATION.md` for detailed test results and outcomes.

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_generator.py::test_report_generation

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Logs

Logs are stored in `logs/automation.log` with format:
```
[2026-07-08 14:30:45] INFO: Starting report generation...
[2026-07-08 14:30:46] INFO: Processing 1,250 records...
[2026-07-08 14:30:48] INFO: Report generated: reports/2026-07-08_sales_report.csv
[2026-07-08 14:30:50] INFO: Email sent successfully to 3 recipients
```

## Error Handling

The script handles:
- ❌ Missing configuration files
- ❌ Invalid data formats
- ❌ Email delivery failures
- ❌ File system errors
- ❌ Network issues

All errors are logged with context for debugging.

## License

MIT License - See LICENSE file for details
