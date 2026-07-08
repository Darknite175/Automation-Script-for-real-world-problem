import unittest
import tempfile
import os
import shutil
import csv
from pathlib import Path
from datetime import datetime
from report_generator import ReportGenerator
import pandas as pd
import yaml


class TestReportGenerator(unittest.TestCase):
    """Test suite for ReportGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.yaml')
        self.data_file = os.path.join(self.test_dir, 'test_data.csv')
        self.log_file = os.path.join(self.test_dir, 'test.log')
        self.report_dir = os.path.join(self.test_dir, 'reports')
        
        # Create sample data
        self._create_sample_data()
        # Create test config
        self._create_test_config()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def _create_sample_data(self):
        """Create sample CSV data for testing."""
        data = {
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'department': ['Sales', 'IT', 'HR', 'Sales', 'IT'],
            'salary': [50000, 60000, 55000, 52000, 65000],
            'date': ['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05']
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, index=False)

    def _create_test_config(self):
        """Create test configuration."""
        config = {
            'email': {
                'enabled': False,
                'sender': 'test@example.com',
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'password': 'test_password',
                'use_tls': True
            },
            'recipients': ['test1@example.com', 'test2@example.com'],
            'data_source': {
                'path': self.data_file,
                'encoding': 'utf-8',
                'has_header': True
            },
            'report': {
                'output_dir': self.report_dir,
                'format': 'csv',
                'include_summary': True,
                'include_timestamp': True,
                'date_format': '%Y-%m-%d',
                'categories': ['sales', 'inventory', 'performance']
            },
            'logging': {
                'level': 'INFO',
                'file': self.log_file,
                'max_file_size': 10485760,
                'backup_count': 5,
                'console_output': False
            },
            'processing': {
                'chunk_size': 1000,
                'timeout_seconds': 300,
                'retry_attempts': 3,
                'retry_delay_seconds': 5
            },
            'notifications': {
                'email_on_success': True,
                'email_on_error': True,
                'include_report_attachment': True,
                'include_summary_stats': True
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)

    def test_initialization(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator(self.config_file)
        self.assertIsNotNone(generator.config)
        self.assertIsNotNone(generator.logger)

    def test_config_loading(self):
        """Test configuration loading."""
        generator = ReportGenerator(self.config_file)
        self.assertEqual(generator.config['email']['sender'], 'test@example.com')
        self.assertEqual(len(generator.config['recipients']), 2)

    def test_missing_config_file(self):
        """Test handling of missing config file."""
        with self.assertRaises(FileNotFoundError):
            ReportGenerator('nonexistent_config.yaml')

    def test_data_reading(self):
        """Test reading data from source."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 5)
        self.assertEqual(list(df.columns), ['id', 'name', 'department', 'salary', 'date'])

    def test_summary_stats_generation(self):
        """Test summary statistics generation."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        stats = generator._generate_summary_stats(df)
        
        self.assertEqual(stats['total_records'], 5)
        self.assertEqual(stats['columns'], 5)
        self.assertIn('timestamp', stats)
        self.assertIn('data_quality', stats)

    def test_report_generation(self):
        """Test report file generation."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        report_file = generator._generate_report(df, 'test')
        
        self.assertIsNotNone(report_file)
        self.assertTrue(os.path.exists(report_file))
        self.assertTrue(report_file.endswith('.csv'))

    def test_report_directory_creation(self):
        """Test automatic report directory creation."""
        generator = ReportGenerator(self.config_file)
        generator._ensure_directories()
        self.assertTrue(os.path.exists(self.report_dir))

    def test_run_success(self):
        """Test successful execution."""
        generator = ReportGenerator(self.config_file)
        success, message = generator.run(no_email=True)
        
        self.assertTrue(success)
        self.assertIn('Report generated', message)

    def test_run_with_empty_data(self):
        """Test handling of empty data."""
        # Create empty CSV
        empty_file = os.path.join(self.test_dir, 'empty_data.csv')
        with open(empty_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
        
        # Update config
        config = self._load_config()
        config['data_source']['path'] = empty_file
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
        
        generator = ReportGenerator(self.config_file)
        success, message = generator.run(no_email=True)
        
        self.assertFalse(success)

    def test_report_file_naming(self):
        """Test report file naming convention."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        report_file = generator._generate_report(df, 'sales')
        
        filename = os.path.basename(report_file)
        today = datetime.now().strftime('%Y-%m-%d')
        self.assertIn(today, filename)
        self.assertIn('sales', filename)

    def test_multiple_report_types(self):
        """Test generating multiple report types."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        
        for report_type in ['sales', 'inventory', 'performance']:
            report_file = generator._generate_report(df, report_type)
            self.assertIsNotNone(report_file)
            self.assertTrue(os.path.exists(report_file))

    def test_logging_setup(self):
        """Test logging configuration."""
        generator = ReportGenerator(self.config_file)
        self.assertIsNotNone(generator.logger)
        self.assertTrue(os.path.exists(self.log_file))

    def test_config_validation(self):
        """Test configuration validation."""
        # Create incomplete config
        incomplete_config = os.path.join(self.test_dir, 'incomplete_config.yaml')
        config = {'email': {'sender': 'test@example.com'}}
        
        with open(incomplete_config, 'w') as f:
            yaml.dump(config, f)
        
        with self.assertRaises(ValueError):
            ReportGenerator(incomplete_config)

    def _load_config(self):
        """Load test config."""
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)


class TestDataProcessing(unittest.TestCase):
    """Test data processing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.yaml')
        self.data_file = os.path.join(self.test_dir, 'test_data.csv')
        self.report_dir = os.path.join(self.test_dir, 'reports')
        
        self._create_sample_data()
        self._create_test_config()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def _create_sample_data(self):
        """Create sample data with various scenarios."""
        data = {
            'id': [1, 2, 3, 4, 5, None, 7],
            'value': [100.5, 200.0, None, 150.25, 300.0, 250.0, 175.0],
            'category': ['A', 'B', 'A', 'C', 'B', 'A', 'C'],
            'active': [True, False, True, True, False, True, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, index=False)

    def _create_test_config(self):
        """Create minimal test config."""
        config = {
            'email': {'enabled': False},
            'recipients': [],
            'data_source': {'path': self.data_file, 'encoding': 'utf-8'},
            'report': {'output_dir': self.report_dir, 'include_summary': True},
            'logging': {'level': 'WARNING', 'file': os.path.join(self.test_dir, 'test.log'), 'console_output': False},
            'processing': {'chunk_size': 1000}
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)

    def test_data_with_missing_values(self):
        """Test handling of missing values in data."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        
        self.assertEqual(len(df), 7)
        self.assertTrue(df.isnull().any().any())

    def test_summary_with_missing_data(self):
        """Test summary generation with missing data."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        stats = generator._generate_summary_stats(df)
        
        self.assertIn('data_quality', stats)
        self.assertIn('missing_values', stats['data_quality'])

    def test_duplicate_detection(self):
        """Test duplicate record detection."""
        generator = ReportGenerator(self.config_file)
        df = generator._read_data_source()
        stats = generator._generate_summary_stats(df)
        
        self.assertIn('duplicates', stats['data_quality'])


if __name__ == '__main__':
    unittest.main()
