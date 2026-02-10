#================================================================================
# FILE: nic_interface.py
#
# Purpose:
# 1. NIC Interface Layer
# 2. Provides abstraction for network interface communication with DUT
# 
# Author: Diksha Ravindran
# Year: Jan - 2025
# version: Not completed yet - Draft 
#================================================================================



import socket
import struct
import time
import logging
from typing import Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Supported communication protocols"""
    TCP = "tcp"
    UDP = "udp"
    RAW_ETHERNET = "raw_ethernet"


@dataclass
class NetworkConfig:
    """Network configuration for DUT communication"""
    interface_name: str = "eth0"  # e.g., eth0, enp0s3
    protocol: ProtocolType = ProtocolType.TCP
    dut_ip: str = "192.168.1.100"
    dut_port: int = 5000
    timeout_ms: int = 1000
    retry_count: int = 3


class NICInterface:
    """
    Network Interface Card abstraction
    Handles low-level communication with DUT over specified NIC
    """
    
    def __init__(self, config: NetworkConfig):
        self.config = config
        self.socket = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to DUT
        Returns True if successful
        """
        try:
            if self.config.protocol == ProtocolType.TCP:
                return self._connect_tcp()
            elif self.config.protocol == ProtocolType.UDP:
                return self._connect_udp()
            elif self.config.protocol == ProtocolType.RAW_ETHERNET:
                return self._connect_raw()
            else:
                logger.error(f"Unsupported protocol: {self.config.protocol}")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close connection to DUT"""
        if self.socket:
            try:
                self.socket.close()
                self.connected = False
                logger.info("Disconnected from DUT")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
    
    def send(self, data: bytes) -> bool:
        """
        Send data to DUT
        Returns True if successful
        """
        if not self.connected:
            logger.error("Not connected to DUT")
            return False
            
        try:
            if self.config.protocol in [ProtocolType.TCP, ProtocolType.UDP]:
                self.socket.sendall(data)
            else:  # Raw Ethernet
                self.socket.send(data)
                
            logger.debug(f"Sent {len(data)} bytes to DUT")
            return True
            
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False
    
    def receive(self, buffer_size: int = 4096) -> Optional[bytes]:
        """
        Receive data from DUT
        Returns received data or None on timeout/error
        """
        if not self.connected:
            logger.error("Not connected to DUT")
            return None
            
        try:
            # Set timeout
            timeout_sec = self.config.timeout_ms / 1000.0
            self.socket.settimeout(timeout_sec)
            
            data = self.socket.recv(buffer_size)
            logger.debug(f"Received {len(data)} bytes from DUT")
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
        expected_size: int = 4096
    ) -> Optional[bytes]:
        """
        Send data and wait for response
        Returns response data or None
        """
        if not self.send(data):
            return None
        return self.receive(expected_size)
    
    # Protocol-specific connection methods
    
    def _connect_tcp(self) -> bool:
        """Connect using TCP"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Bind to specific interface if needed
        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, 
        #                        self.config.interface_name.encode())
        
        logger.info(f"Connecting to {self.config.dut_ip}:{self.config.dut_port} via TCP")
        
        for attempt in range(self.config.retry_count):
            try:
                self.socket.connect((self.config.dut_ip, self.config.dut_port))
                self.connected = True
                logger.info("TCP connection established")
                return True
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(0.5)
                
        return False
    
    def _connect_udp(self) -> bool:
        """Connect using UDP"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # UDP is connectionless, but we can set the default destination
        self.socket.connect((self.config.dut_ip, self.config.dut_port))
        self.connected = True
        logger.info(f"UDP socket configured for {self.config.dut_ip}:{self.config.dut_port}")
        return True
    
    def _connect_raw(self) -> bool:
        """Connect using raw Ethernet sockets"""
        # Requires root/admin privileges
        try:
            # AF_PACKET for Linux, might need different approach for Windows
            self.socket = socket.socket(
                socket.AF_PACKET, 
                socket.SOCK_RAW, 
                socket.htons(0x0003)  # ETH_P_ALL
            )
            
            # Bind to specific interface
            self.socket.bind((self.config.interface_name, 0))
            self.connected = True
            logger.info(f"Raw Ethernet socket bound to {self.config.interface_name}")
            return True
            
        except PermissionError:
            logger.error("Raw sockets require root/administrator privileges")
            return False
        except Exception as e:
            logger.error(f"Raw socket creation failed: {e}")
            return False
    
    def get_interface_info(self) -> dict:
        """Get information about the network interface"""
        import netifaces
        
        try:
            addrs = netifaces.ifaddresses(self.config.interface_name)
            return {
                'interface': self.config.interface_name,
                'ipv4': addrs.get(netifaces.AF_INET, [{}])[0].get('addr', 'N/A'),
                'mac': addrs.get(netifaces.AF_LINK, [{}])[0].get('addr', 'N/A')
            }
        except Exception as e:
            logger.error(f"Failed to get interface info: {e}")
            return {'error': str(e)}


class PacketBuilder:
    """
    Helper class for building custom packets
    Useful for protocol testing
    """
    
    @staticmethod
    def build_ethernet_frame(
        dst_mac: str,
        src_mac: str,
        payload: bytes,
        ethertype: int = 0x0800  # IPv4
    ) -> bytes:
        """Build raw Ethernet frame"""
        dst = bytes.fromhex(dst_mac.replace(':', ''))
        src = bytes.fromhex(src_mac.replace(':', ''))
        eth_type = struct.pack('!H', ethertype)
        return dst + src + eth_type + payload
    
    @staticmethod
    def build_ip_header(
        src_ip: str,
        dst_ip: str,
        protocol: int = 6,  # TCP
        payload_length: int = 0
    ) -> bytes:
        """Build IPv4 header"""
        # Simplified IP header (20 bytes)
        version_ihl = (4 << 4) | 5  # IPv4, 5 words
        total_length = 20 + payload_length
        
        header = struct.pack(
            '!BBHHHBBH4s4s',
            version_ihl, 0,  # Version/IHL, TOS
            total_length, 0, 0,  # Total length, ID, Flags/Fragment
            64, protocol, 0,  # TTL, Protocol, Checksum (0 for now)
            socket.inet_aton(src_ip),
            socket.inet_aton(dst_ip)
        )
        return header
    
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """Calculate IP/TCP checksum"""
        checksum = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) + data[i + 1]
            else:
                word = data[i] << 8
            checksum += word
            
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum = ~checksum & 0xFFFF
        return checksum


def list_available_interfaces() -> List[str]:
    """List all available network interfaces"""
    try:
        import netifaces
        return netifaces.interfaces()
    except ImportError:
        logger.warning("netifaces not installed, using basic socket method")
        # Fallback method
        import os
        if os.name == 'nt':  # Windows
            # Would need different approach for Windows
            return []
        else:  # Linux/Unix
            interfaces = []
            for line in open('/proc/net/dev'):
                if ':' in line:
                    interfaces.append(line.split(':')[0].strip())
            return interfaces
