#================================================================================
# FILE: dut_connection.py
#
# Purpose:
# 1. DUT Connection Module
# 2. Handles TCP/UDP communication and CLI command execution with embedded devices
# 
# Author: Diksha Ravindran
# Year: Jan - 2025
# version: Not completed yet - Draft 
#================================================================================


import socket
import time
import logging
import re
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Communication protocol types"""
    TCP = "tcp"
    UDP = "udp"


@dataclass
class DUTConfig:
    """DUT connection configuration"""
    ip: str = "192.168.1.100"
    port: int = 5000
    protocol: ProtocolType = ProtocolType.TCP
    timeout_ms: int = 1000
    cli_port: int = 23  # Telnet/CLI port
    cli_prompt: str = "DUT>"  # Expected CLI prompt
    cli_username: str = ""
    cli_password: str = ""


class DUTConnection:
    """
    Main DUT connection handler
    Manages TCP/UDP communication and CLI command execution
    """
    
    def __init__(self, config: DUTConfig):
        self.config = config
        self.data_socket = None
        self.cli_socket = None
        self.connected = False
        self.cli_authenticated = False
        
    def connect(self) -> bool:
        """
        Establish connection to DUT
        Returns True if successful
        """
        try:
            logger.info(f"Connecting to DUT at {self.config.ip}:{self.config.port}")
            
            if self.config.protocol == ProtocolType.TCP:
                self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.data_socket.connect((self.config.ip, self.config.port))
            else:  # UDP
                self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.data_socket.connect((self.config.ip, self.config.port))
            
            # Set timeout
            timeout_sec = self.config.timeout_ms / 1000.0
            self.data_socket.settimeout(timeout_sec)
            
            self.connected = True
            logger.info("Data connection established")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close all connections"""
        if self.data_socket:
            try:
                self.data_socket.close()
                logger.info("Data connection closed")
            except:
                pass
            self.data_socket = None
            
        if self.cli_socket:
            try:
                self.cli_socket.close()
                logger.info("CLI connection closed")
            except:
                pass
            self.cli_socket = None
            
        self.connected = False
        self.cli_authenticated = False
    
    def send(self, data: bytes) -> bool:
        """
        Send data to DUT
        Returns True if successful
        """
        if not self.connected or not self.data_socket:
            logger.error("Not connected to DUT")
            return False
        
        try:
            if self.config.protocol == ProtocolType.TCP:
                self.data_socket.sendall(data)
            else:  # UDP
                self.data_socket.send(data)
            
            logger.debug(f"Sent {len(data)} bytes: {data[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False
    
    def receive(self, buffer_size: int = 4096) -> Optional[bytes]:
        """
        Receive data from DUT
        Returns received data or None on timeout/error
        """
        if not self.connected or not self.data_socket:
            logger.error("Not connected to DUT")
            return None
        
        try:
            data = self.data_socket.recv(buffer_size)
            logger.debug(f"Received {len(data)} bytes: {data[:50]}...")
            return data
            
        except socket.timeout:
            logger.warning(f"Receive timeout ({self.config.timeout_ms}ms)")
            return None
        except Exception as e:
            logger.error(f"Receive failed: {e}")
            return None
    
    def send_and_receive(
        self, 
        data: bytes, 
        expected_size: int = 4096,
        measure_latency: bool = False
    ) -> Tuple[Optional[bytes], Optional[float]]:
        """
        Send data and wait for response
        
        Args:
            data: Data to send
            expected_size: Expected response size
            measure_latency: Whether to measure round-trip time
            
        Returns:
            Tuple of (response_data, latency_ms)
        """
        start_time = time.time() if measure_latency else None
        
        if not self.send(data):
            return None, None
        
        response = self.receive(expected_size)
        
        latency = None
        if measure_latency and start_time:
            latency = (time.time() - start_time) * 1000  # Convert to ms
            logger.debug(f"Round-trip latency: {latency:.2f}ms")
        
        return response, latency
    
    # CLI Command Execution Methods
    
    def connect_cli(self) -> bool:
        """
        Establish CLI connection (typically Telnet/SSH)
        Returns True if successful
        """
        try:
            logger.info(f"Connecting to DUT CLI at {self.config.ip}:{self.config.cli_port}")
            
            self.cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cli_socket.connect((self.config.ip, self.config.cli_port))
            self.cli_socket.settimeout(self.config.timeout_ms / 1000.0)
            
            # Wait for initial prompt/banner
            time.sleep(0.5)
            self._cli_receive_until_prompt()
            
            # Authenticate if credentials provided
            if self.config.cli_username:
                if not self._cli_authenticate():
                    logger.error("CLI authentication failed")
                    return False
            
            self.cli_authenticated = True
            logger.info("CLI connection established")
            return True
            
        except Exception as e:
            logger.error(f"CLI connection failed: {e}")
            return False
    
    def execute_cli_command(
        self, 
        command: str, 
        timeout_ms: Optional[int] = None
    ) -> Optional[str]:
        """
        Execute a CLI command on the DUT
        
        Args:
            command: Command to execute
            timeout_ms: Optional timeout override
            
        Returns:
            Command output as string, or None on error
        """
        if not self.cli_socket:
            logger.error("CLI not connected")
            return None
        
        try:
            # Send command
            cmd_bytes = (command + "\n").encode('utf-8')
            self.cli_socket.sendall(cmd_bytes)
            logger.debug(f"Executing CLI command: {command}")
            
            # Set temporary timeout if provided
            if timeout_ms:
                self.cli_socket.settimeout(timeout_ms / 1000.0)
            
            # Receive response until prompt
            output = self._cli_receive_until_prompt()
            
            # Restore original timeout
            if timeout_ms:
                self.cli_socket.settimeout(self.config.timeout_ms / 1000.0)
            
            # Clean up output (remove echo and prompt)
            output = self._clean_cli_output(output, command)
            
            logger.debug(f"Command output ({len(output)} chars): {output[:100]}...")
            return output
            
        except Exception as e:
            logger.error(f"CLI command execution failed: {e}")
            return None
    
    def execute_cli_commands(self, commands: List[str]) -> List[str]:
        """
        Execute multiple CLI commands
        
        Args:
            commands: List of commands to execute
            
        Returns:
            List of command outputs
        """
        results = []
        for cmd in commands:
            output = self.execute_cli_command(cmd)
            results.append(output if output else "")
        return results
    
    def parse_cli_output(
        self, 
        output: str, 
        pattern: str
    ) -> Optional[Dict[str, str]]:
        """
        Parse CLI output using regex pattern
        
        Args:
            output: CLI command output
            pattern: Regex pattern with named groups
            
        Returns:
            Dictionary of matched groups or None
        """
        try:
            match = re.search(pattern, output, re.MULTILINE | re.DOTALL)
            if match:
                return match.groupdict()
            return None
        except Exception as e:
            logger.error(f"Pattern matching failed: {e}")
            return None
    
    # Private helper methods
    
    def _cli_authenticate(self) -> bool:
        """Authenticate CLI session"""
        try:
            # Look for username prompt
            prompt = self._cli_receive(1024, timeout=2.0)
            
            if "username" in prompt.lower() or "login" in prompt.lower():
                self.cli_socket.sendall((self.config.cli_username + "\n").encode())
                time.sleep(0.2)
            
            # Look for password prompt
            prompt = self._cli_receive(1024, timeout=2.0)
            
            if "password" in prompt.lower():
                self.cli_socket.sendall((self.config.cli_password + "\n").encode())
                time.sleep(0.5)
            
            # Check for successful login
            response = self._cli_receive(1024, timeout=2.0)
            return self.config.cli_prompt in response or ">" in response or "#" in response
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _cli_receive_until_prompt(self, max_wait: float = 5.0) -> str:
        """Receive data until CLI prompt appears"""
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                chunk = self.cli_socket.recv(1024).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                output += chunk
                
                # Check if prompt appeared
                if self.config.cli_prompt in output or output.strip().endswith('>') or output.strip().endswith('#'):
                    break
                    
            except socket.timeout:
                break
            except Exception as e:
                logger.error(f"CLI receive error: {e}")
                break
        
        return output
    
    def _cli_receive(self, buffer_size: int, timeout: float = None) -> str:
        """Receive data from CLI socket"""
        if timeout:
            old_timeout = self.cli_socket.gettimeout()
            self.cli_socket.settimeout(timeout)
        
        try:
            data = self.cli_socket.recv(buffer_size).decode('utf-8', errors='ignore')
            return data
        finally:
            if timeout:
                self.cli_socket.settimeout(old_timeout)
    
    def _clean_cli_output(self, output: str, command: str) -> str:
        """Clean CLI output by removing echo and prompt"""
        # Remove command echo
        if command in output:
            output = output.replace(command, "", 1)
        
        # Remove prompt at the end
        lines = output.split('\n')
        if lines and (self.config.cli_prompt in lines[-1] or 
                     lines[-1].strip().endswith('>') or 
                     lines[-1].strip().endswith('#')):
            lines = lines[:-1]
        
        # Remove empty lines at start/end
        output = '\n'.join(lines).strip()
        
        return output
    
    # Context manager support
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class PacketBuilder:
    """
    Helper class for building custom protocol packets
    """
    
    @staticmethod
    def build_packet(
        command: int,
        payload: bytes = b'',
        sequence_num: int = 0,
        include_checksum: bool = True
    ) -> bytes:
        """
        Build a custom packet with header
        
        Format:
        [START_MARKER][COMMAND][SEQ_NUM][LENGTH][PAYLOAD][CHECKSUM]
        2 bytes       1 byte    2 bytes  2 bytes variable 2 bytes
        """
        import struct
        
        START_MARKER = 0xAA55
        packet = struct.pack('>H', START_MARKER)  # Start marker
        packet += struct.pack('B', command)        # Command byte
        packet += struct.pack('>H', sequence_num)  # Sequence number
        packet += struct.pack('>H', len(payload))  # Payload length
        packet += payload                          # Payload
        
        if include_checksum:
            checksum = PacketBuilder.calculate_checksum(packet)
            packet += struct.pack('>H', checksum)
        
        return packet
    
    @staticmethod
    def parse_packet(data: bytes) -> Optional[Dict]:
        """
        Parse received packet
        
        Returns:
            Dictionary with packet fields or None if invalid
        """
        import struct
        
        if len(data) < 9:  # Minimum packet size
            return None
        
        try:
            marker = struct.unpack('>H', data[0:2])[0]
            if marker != 0xAA55:
                return None
            
            command = struct.unpack('B', data[2:3])[0]
            seq_num = struct.unpack('>H', data[3:5])[0]
            length = struct.unpack('>H', data[5:7])[0]
            payload = data[7:7+length]
            
            result = {
                'command': command,
                'sequence': seq_num,
                'length': length,
                'payload': payload
            }
            
            # Verify checksum if present
            if len(data) >= 7 + length + 2:
                received_checksum = struct.unpack('>H', data[7+length:9+length])[0]
                calculated_checksum = PacketBuilder.calculate_checksum(data[:7+length])
                result['checksum_valid'] = (received_checksum == calculated_checksum)
            
            return result
            
        except Exception as e:
            logger.error(f"Packet parsing failed: {e}")
            return None
    
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """Calculate simple 16-bit checksum"""
        checksum = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) + data[i + 1]
            else:
                word = data[i] << 8
            checksum += word
        
        # Handle overflow
        while checksum >> 16:
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        
        return (~checksum) & 0xFFFF


class LatencyMeasurement:
    """
    Helper class for precise latency measurements
    """
    
    def __init__(self):
        self.measurements = []
        self.start_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.perf_counter()
    
    def stop(self) -> float:
        """
        Stop timing and record
        Returns latency in milliseconds
        """
        if self.start_time is None:
            return 0.0
        
        latency_ms = (time.perf_counter() - self.start_time) * 1000
        self.measurements.append(latency_ms)
        self.start_time = None
        return latency_ms
    
    def get_statistics(self) -> Dict[str, float]:
        """Get latency statistics"""
        if not self.measurements:
            return {}
        
        return {
            'min_ms': min(self.measurements),
            'max_ms': max(self.measurements),
            'avg_ms': sum(self.measurements) / len(self.measurements),
            'count': len(self.measurements)
        }
    
    def reset(self):
        """Reset measurements"""
        self.measurements = []
        self.start_time = None
