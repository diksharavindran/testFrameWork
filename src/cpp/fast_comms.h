/**================================================================================
* FILE: fast_comms.h

* Purpose:
* 1. Implementation of high-performance DUT communication
 
* Author: Diksha Ravindran
* Year: Jan - 2026
* version: Not completed yet - Draft 
================================================================================
*/
#ifndef FAST_COMMS_H
#define FAST_COMMS_H

#include <cstdint>
#include <vector>
#include <string>
#include <chrono>

namespace embedded_test {
    //Packet statistics structure
    struct PacketStats {
    uint64_t packets_sent;
    uint64_t packets_received;
    uint64_t bytes_sent;
    uint64_t bytes_received;
    uint64_t errors;
    double avg_latency_us;  // microseconds
    
    PacketStats() : packets_sent(0), packets_received(0), 
                    bytes_sent(0), bytes_received(0), 
                    errors(0), avg_latency_us(0.0) {}
};
//Communication result
struct CommResult {
    bool success;
    std::vector<uint8_t> data;
    uint64_t latency_us;
    std::string error_message;
    
    CommResult() : success(false), latency_us(0) {}
};

//Fast communication handler

class FastComms {
public:
//Constructor
//@param interface_name Network interface (e.g., "eth0")
//@param timeout_ms Timeout in milliseconds
FastComms(const std::string& interface_name, uint32_t timeout_ms = 1000);
//Destructor
~FastComms();

//Initialize the communication channel
//return true if successful

bool initialize();

//Close the communication channel

void close();

//Send raw packet
//param data Packet data
//return true if sent successfully

bool send_packet(const std::vector<uint8_t>& data);

//Receive raw packet with timeout
//param buffer Buffer to store received data
//param max_size Maximum size to receive
//return Number of bytes received, -1 on error

int receive_packet(std::vector<uint8_t>& buffer, size_t max_size = 4096);

//Send packet and wait for response
//param request Request data
//param response Buffer for response
//return Communication result with latency

CommResult send_and_receive(const std::vector<uint8_t>& request, 
                                 std::vector<uint8_t>& response);

//Burst send multiple packets
//Optimized for high-throughput scenarios
//param packets Vector of packets to send
//return Number of packets successfully sent

int burst_send(const std::vector<std::vector<uint8_t>>& packets);

//Measure round-trip latency
//Sends ping packet and measures response time
//param payload Ping payload
//return Latency in microseconds, -1 on error

int64_t measure_latency(const std::vector<uint8_t>& payload);

//Stress test - send packets at maximum rate
//param duration_ms Duration in milliseconds
//param packet_size Size of each packet
//return Statistics about the stress test

PacketStats stress_test(uint32_t duration_ms, size_t packet_size = 64);

//Get communication statistics
//return Current statistics

PacketStats get_statistics() const;

//Reset statistics counters

void reset_statistics();

//Set timeout
//param timeout_ms Timeout in milliseconds

void set_timeout(uint32_t timeout_ms);

//Check if interface is ready
//return true if ready for communication

bool is_ready() const;

private:
    std::string interface_name_;
    uint32_t timeout_ms_;
    int socket_fd_;
    bool initialized_;
    PacketStats stats_;
    
    // Helper methods
    int create_raw_socket();
    int bind_to_interface();
    void update_stats(bool sent, size_t bytes, uint64_t latency_us);
    uint64_t get_timestamp_us();
};

//Packet validator
//Fast checksum and validation operations

class PacketValidator {
public:

    //Calculate CRC32 checksum
    //param data Data to checksum
    //return CRC32 value

    static uint32_t calculate_crc32(const std::vector<uint8_t>& data);
    
    
     //Verify packet integrity
     //param packet Packet with checksum
     //param expected_crc Expected CRC value
     //return true if valid
    
    static bool verify_packet(const std::vector<uint8_t>& packet, uint32_t expected_crc);
    
    
     //Calculate simple checksum (faster but less robust)
     //param data Data to checksum
     //return Checksum value
    
    static uint16_t calculate_simple_checksum(const std::vector<uint8_t>& data);
};

//Performance monitor
//Track timing and throughput metrics

class PerformanceMonitor {
public:
    PerformanceMonitor();
    
    void start_measurement();
    void stop_measurement();
    
    double get_elapsed_ms() const;
    double get_throughput_mbps(size_t bytes_transferred) const;
    
private:
    std::chrono::high_resolution_clock::time_point start_time_;
    std::chrono::high_resolution_clock::time_point end_time_;
};

} // namespace embedded_test

#endif // FAST_COMMS_H






