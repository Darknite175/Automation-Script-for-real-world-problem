#!/usr/bin/env python3
"""
Automated Report Generation & Distribution System
Main automation script that generates reports and sends them via email.
"""

import os
import sys
import argparse
import logging
import smtplib
import csv
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import yaml
import pandas as pd
from typing import List, Dict, Optional, Tuple


class ReportGenerator:
    """Main class for automated report generation and distribution."""

    def __init__(self, config_path: str = "config.yaml", verbose: bool = False):
        """
        Initialize the report generator.
        
        Args:
            config_path: Path to YAML configuration file
            verbose: Enable verbose logging
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging(verbose)
        self._validate_config()
        self.logger.info("Report generator initialized successfully")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")

    def _setup_logging(self, verbose: bool = False) -> logging.Logger:
        """Configure logging system."""
        log_dir = Path(self.config.get('logging', {}).get('file', 'logs/automation.log')).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(__name__)
        level = logging.DEBUG if verbose else logging.INFO
        logger.setLevel(level)

        # File handler
        log_file = self.config.get('logging', {}).get('file', 'logs/automation.log')
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        if self.config.get('logging', {}).get('console_output', True):
            logger.addHandler(ch)

        return logger

    def _validate_config(self):
        """Validate required configuration fields."""
        required_keys = ['email', 'recipients', 'data_source', 'report', 'logging']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")
        
        self.logger.debug("Configuration validation passed")

    def _ensure_directories(self):
        """Create necessary directories."""
        report_dir = Path(self.config['report']['output_dir'])
        report_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Report directory ensured: {report_dir}")

    def _read_data_source(self) -> Optional[pd.DataFrame]:
        """
        Read data from source file.
        
        Returns:
            DataFrame with source data or None if failed
        """
        try:
            source_path = self.config['data_source']['path']
            encoding = self.config['data_source'].get('encoding', 'utf-8')
            
            if not os.path.exists(source_path):
                self.logger.error(f"Data source file not found: {source_path}")
                return None
            
            df = pd.read_csv(source_path, encoding=encoding)
            self.logger.info(f"Read {len(df)} records from source: {source_path}")
            return df
        except Exception as e:
            self.logger.error(f"Error reading data source: {e}")
            return None

    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for the report."""
        try:
            stats = {
                'total_records': len(df),
                'columns': len(df.columns),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_quality': {
                    'missing_values': df.isnull().sum().to_dict(),
                    'duplicates': len(df[df.duplicated()])
                }
            }
            return stats
        except Exception as e:
            self.logger.error(f"Error generating summary stats: {e}")
            return {}

    def _generate_report(self, df: pd.DataFrame, category: str = 'general') -> Optional[str]:
        """
        Generate report file from data.
        
        Args:
            df: DataFrame to process
            category: Report category
            
        Returns:
            Path to generated report or None if failed
        """
        try:
            self._ensure_directories()
            
            timestamp = datetime.now().strftime('%Y-%m-%d')
            output_dir = Path(self.config['report']['output_dir'])
            report_file = output_dir / f"{timestamp}_{category}_report.csv"
            
            # Save report
            df.to_csv(report_file, index=False)
            self.logger.info(f"Report generated: {report_file}")
            
            # Generate summary if enabled
            if self.config['report'].get('include_summary', False):
                summary = self._generate_summary_stats(df)
                self.logger.info(f"Summary: {summary['total_records']} records processed")
            
            return str(report_file)
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return None

    def _send_email(self, report_file: str, recipients: List[str]) -> bool:
        """
        Send report via email.
        
        Args:
            report_file: Path to report file
            recipients: List of recipient email addresses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            email_config = self.config['email']
            
            if not email_config.get('enabled', True):
                self.logger.info("Email notifications disabled")
                return True
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender']
            msg['To'] = ', '.join(recipients)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = f"Automated Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Body
            body = f"""
Dear Stakeholder,

Please find attached the automated report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

This is an automated message. Please do not reply.

Best regards,
Automation System
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report
            if self.config['report'].get('include_report_attachment', True):
                with open(report_file, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {Path(report_file).name}'
                    )
                    msg.attach(part)
            
            # Send email
            password = os.getenv('EMAIL_PASSWORD') or email_config.get('password')
            if not password:
                self.logger.warning("Email password not configured, skipping email send")
                return False
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                server.login(email_config['sender'], password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {len(recipients)} recipient(s)")
            return True
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False

    def run(self, no_email: bool = False, report_type: str = 'general') -> Tuple[bool, str]:
        """
        Main execution method.
        
        Args:
            no_email: Skip email sending (dry run)
            report_type: Type of report to generate
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting automated report generation...")
            self.logger.info("=" * 60)
            
            # Read data
            df = self._read_data_source()
            if df is None or df.empty:
                message = "No data to process"
                self.logger.error(message)
                return False, message
            
            # Generate report
            report_file = self._generate_report(df, report_type)
            if report_file is None:
                message = "Failed to generate report"
                self.logger.error(message)
                return False, message
            
            # Send email
            if not no_email:
                recipients = self.config.get('recipients', [])
                if recipients:
                    self._send_email(report_file, recipients)
                else:
                    self.logger.warning("No recipients configured")
            else:
                self.logger.info("Email sending skipped (dry run mode)")
            
            self.logger.info("=" * 60)
            self.logger.info("Report generation completed successfully")
            self.logger.info("=" * 60)
            
            message = f"Report generated: {report_file}"
            return True, message
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(error_msg)
            return False, error_msg


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated Report Generation & Distribution System'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--report-type',
        default='general',
        help='Type of report to generate (default: general)'
    )
    parser.add_argument(
        '--no-email',
        action='store_true',
        help='Skip email notifications (dry run)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    try:
        generator = ReportGenerator(args.config, args.verbose)
        success, message = generator.run(args.no_email, args.report_type)
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
