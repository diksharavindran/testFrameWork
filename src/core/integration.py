#================================================================================
# FILE: integration.py
#
# Purpose:
# 1. Framework Integration
# 2. Connects DUT communication with the test framewor
# 

# Author: Diksha Ravindran
# Year: Jan - 2026
#================================================================================


import logging
from pathlib import Path
import yaml

from src.network.dut_connection import DUTConnection, DUTConfig, ProtocolType
from src.core.scheduler import TestScheduler


logger = logging.getLogger(__name__)


class FrameworkConfig:
    """Load and manage framework configuration"""
    
    def __init__(self, config_file: str = "config/framework_config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {self.config_file}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'network': {
                'interface': 'eth0',
                'protocol': 'tcp',
                'dut': {
                    'ip': '192.168.1.100',
                    'port': 5000
                },
                'timeout': 1000,
                'retry_count': 3
            },
            'execution': {
                'mode': 'sequential',
                'workers': 4,
                'stop_on_failure': False
            }
        }
    
    def get_dut_config(self) -> DUTConfig:
        """Get DUT configuration object"""
        net_config = self.config.get('network', {})
        dut_config = net_config.get('dut', {})
        
        # Parse protocol
        protocol_str = net_config.get('protocol', 'tcp').lower()
        protocol = ProtocolType.TCP if protocol_str == 'tcp' else ProtocolType.UDP
        
        return DUTConfig(
            ip=dut_config.get('ip', '192.168.1.100'),
            port=dut_config.get('port', 5000),
            protocol=protocol,
            timeout_ms=net_config.get('timeout', 1000),
            cli_port=dut_config.get('cli_port', 23),
            cli_prompt=dut_config.get('cli_prompt', 'DUT>'),
            cli_username=dut_config.get('cli_username', ''),
            cli_password=dut_config.get('cli_password', '')
        )


class TestRunner:
    """
    High-level test runner that integrates all components
    """
    
    def __init__(self, config_file: str = "config/framework_config.yaml"):
        self.framework_config = FrameworkConfig(config_file)
        self.dut_connection = None
        
    def setup_dut_connection(self) -> bool:
        """
        Setup connection to DUT
        Returns True if successful
        """
        dut_config = self.framework_config.get_dut_config()
        
        logger.info(f"Setting up DUT connection to {dut_config.ip}:{dut_config.port}")
        logger.info(f"Protocol: {dut_config.protocol.value.upper()}")
        
        self.dut_connection = DUTConnection(dut_config)
        
        if self.dut_connection.connect():
            logger.info("✓ DUT connection established")
            return True
        else:
            logger.error("✗ Failed to connect to DUT")
            return False
    
    def run_with_dut(self, scheduler: TestScheduler):
        """
        Setup DUT connection and inject into scheduler
        
        Args:
            scheduler: TestScheduler instance
        """
        if self.setup_dut_connection():
            scheduler.set_dut_connection(self.dut_connection)
            logger.info("DUT connection injected into test scheduler")
        else:
            logger.warning("Running tests without DUT connection (will use mocks)")
    
    def cleanup(self):
        """Cleanup DUT connection"""
        if self.dut_connection:
            self.dut_connection.disconnect()
            logger.info("DUT connection closed")


# Convenience function for use in CLI
def create_test_runner(config_file: str = "config/framework_config.yaml") -> TestRunner:
    """Create and return a configured test runner"""
    return TestRunner(config_file)

