/**================================================================================
* FILE: fast_comms.cpp

* Purpose:
* 1. Implementation of high-performance DUT communication
 
* Author: Diksha Ravindran
* Year: Jan - 2026
* version: Not completed yet - Draft 
================================================================================
*/
#include "fast_comms.h"
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <linux/if_packet.h>
#include <net/ethernet.h>
#include <unistd.h>
#include <cstring>
#include <stdexcept>
#include <iostream>

namespace embedded_test {

FastComms::FastComms(const std::string& interface_name, uint32_t timeout_ms)
    : interface_name_(interface_name),
      timeout_ms_(timeout_ms),
      socket_fd_(-1),
      initialized_(false) {
}

FastComms::~FastComms() {
    close();
}

bool FastComms::initialize() {
    if (initialized_) {
        return true;
    }
    
    // Create raw socket
    socket_fd_ = create_raw_socket();
    if (socket_fd_ < 0) {
        return false;
    }
    
    // Bind to interface
    if (bind_to_interface() < 0) {
        ::close(socket_fd_);
        socket_fd_ = -1;
        return false;
    }
    
    // Set timeout
    struct timeval tv;
    tv.tv_sec = timeout_ms_ / 1000;
    tv.tv_usec = (timeout_ms_ % 1000) * 1000;
    
    if (setsockopt(socket_fd_, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) < 0) {
        std::cerr << "Warning: Failed to set receive timeout" << std::endl;
    }
    
    initialized_ = true;
    return true;
}

void FastComms::close() {
    if (socket_fd_ >= 0) {
        ::close(socket_fd_);
        socket_fd_ = -1;
    }
    initialized_ = false;
}

bool FastComms::send_packet(const std::vector<uint8_t>& data) {
    if (!initialized_ || socket_fd_ < 0) {
        return false;
    }
    
    uint64_t start_time = get_timestamp_us();
    
    ssize_t sent = send(socket_fd_, data.data(), data.size(), 0);
    
    if (sent < 0) {
        stats_.errors++;
        return false;
    }
    
    uint64_t latency = get_timestamp_us() - start_time;
    update_stats(true, sent, latency);
    
    return sent == static_cast<ssize_t>(data.size());
}

int FastComms::receive_packet(std::vector<uint8_t>& buffer, size_t max_size) {
    if (!initialized_ || socket_fd_ < 0) {
        return -1;
    }
    
    buffer.resize(max_size);
    
    ssize_t received = recv(socket_fd_, buffer.data(), max_size, 0);
    
    if (received < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            
            return 0;
        }
        stats_.errors++;
        return -1;
    }
    
    buffer.resize(received);
    update_stats(false, received, 0);
    
    return received;
}

CommResult FastComms::send_and_receive(const std::vector<uint8_t>& request,
                                       std::vector<uint8_t>& response) {
    CommResult result;
    
    uint64_t start_time = get_timestamp_us();
    
    // Send request
    if (!send_packet(request)) {
        result.error_message = "Failed to send request";
        return result;
    }
    
    // Receive response
    int received = receive_packet(response);
    
    if (received < 0) {
        result.error_message = "Failed to receive response";
        return result;
    }
    
    if (received == 0) {
        result.error_message = "Response timeout";
        return result;
    }
    
    result.success = true;
    result.data = response;
    result.latency_us = get_timestamp_us() - start_time;
    
    return result;
}

int FastComms::burst_send(const std::vector<std::vector<uint8_t>>& packets) {
    int sent_count = 0;
    
    for (const auto& packet : packets) {
        if (send_packet(packet)) {
            sent_count++;
        }
    }
    
    return sent_count;
}

int64_t FastComms::measure_latency(const std::vector<uint8_t>& payload) {
    std::vector<uint8_t> response;
    CommResult result = send_and_receive(payload, response);
    
    if (result.success) {
        return result.latency_us;
    }
    
    return -1;
}

PacketStats FastComms::stress_test(uint32_t duration_ms, size_t packet_size) {
    PacketStats test_stats;
    
    // Create test packet
    std::vector<uint8_t> test_packet(packet_size, 0xAA);
    
    uint64_t start_time = get_timestamp_us();
    uint64_t end_time = start_time + (duration_ms * 1000);
    
    while (get_timestamp_us() < end_time) {
        if (send_packet(test_packet)) {
            test_stats.packets_sent++;
            test_stats.bytes_sent += packet_size;
        } else {
            test_stats.errors++;
        }
    }
    
    uint64_t total_time_us = get_timestamp_us() - start_time;
    
    // Calculate throughput
    if (total_time_us > 0) {
        double time_sec = total_time_us / 1000000.0;
        double mbps = (test_stats.bytes_sent * 8.0) / (time_sec * 1000000.0);
        std::cout << "Stress test: " << test_stats.packets_sent 
                  << " packets, " << mbps << " Mbps" << std::endl;
    }
    
    return test_stats;
}

PacketStats FastComms::get_statistics() const {
    return stats_;
}

void FastComms::reset_statistics() {
    stats_ = PacketStats();
}

void FastComms::set_timeout(uint32_t timeout_ms) {
    timeout_ms_ = timeout_ms;
    
    if (initialized_ && socket_fd_ >= 0) {
        struct timeval tv;
        tv.tv_sec = timeout_ms_ / 1000;
        tv.tv_usec = (timeout_ms_ % 1000) * 1000;
        setsockopt(socket_fd_, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    }
}

bool FastComms::is_ready() const {
    return initialized_ && socket_fd_ >= 0;
}

// Private helper methods

int FastComms::create_raw_socket() {
    int sockfd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    
    if (sockfd < 0) {
        std::cerr << "Failed to create raw socket (need root privileges)" << std::endl;
        return -1;
    }
    
    return sockfd;
}

int FastComms::bind_to_interface() {
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, interface_name_.c_str(), IFNAMSIZ - 1);
    
    // Get interface index
    if (ioctl(socket_fd_, SIOCGIFINDEX, &ifr) < 0) {
        std::cerr << "Failed to get interface index for " << interface_name_ << std::endl;
        return -1;
    }
    
    // Bind socket to interface
    struct sockaddr_ll sll;
    memset(&sll, 0, sizeof(sll));
    sll.sll_family = AF_PACKET;
    sll.sll_ifindex = ifr.ifr_ifindex;
    sll.sll_protocol = htons(ETH_P_ALL);
    
    if (bind(socket_fd_, (struct sockaddr*)&sll, sizeof(sll)) < 0) {
        std::cerr << "Failed to bind to interface " << interface_name_ << std::endl;
        return -1;
    }
    
    return 0;
}

void FastComms::update_stats(bool sent, size_t bytes, uint64_t latency_us) {
    if (sent) {
        stats_.packets_sent++;
        stats_.bytes_sent += bytes;
    } else {
        stats_.packets_received++;
        stats_.bytes_received += bytes;
    }
    
    // Update average latency (simple moving average)
    if (latency_us > 0) {
        stats_.avg_latency_us = (stats_.avg_latency_us * 0.9) + (latency_us * 0.1);
    }
}

uint64_t FastComms::get_timestamp_us() {
    auto now = std::chrono::high_resolution_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
}

// PacketValidator Implementation

uint32_t PacketValidator::calculate_crc32(const std::vector<uint8_t>& data) {
    uint32_t crc = 0xFFFFFFFF;
    
    for (uint8_t byte : data) {
        crc ^= byte;
        for (int i = 0; i < 8; i++) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0xEDB88320;
            } else {
                crc >>= 1;
            }
        }
    }
    
    return ~crc;
}

bool PacketValidator::verify_packet(const std::vector<uint8_t>& packet, 
                                    uint32_t expected_crc) {
    return calculate_crc32(packet) == expected_crc;
}

uint16_t PacketValidator::calculate_simple_checksum(const std::vector<uint8_t>& data) {
    uint32_t sum = 0;
    
    for (size_t i = 0; i < data.size(); i += 2) {
        uint16_t word = data[i] << 8;
        if (i + 1 < data.size()) {
            word |= data[i + 1];
        }
        sum += word;
    }
    
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    
    return ~sum & 0xFFFF;
}

// PerformanceMonitor Implementation

PerformanceMonitor::PerformanceMonitor() {
}

void PerformanceMonitor::start_measurement() {
    start_time_ = std::chrono::high_resolution_clock::now();
}

void PerformanceMonitor::stop_measurement() {
    end_time_ = std::chrono::high_resolution_clock::now();
}

double PerformanceMonitor::get_elapsed_ms() const {
    auto duration = end_time_ - start_time_;
    return std::chrono::duration<double, std::milli>(duration).count();
}

double PerformanceMonitor::get_throughput_mbps(size_t bytes_transferred) const {
    double elapsed_sec = get_elapsed_ms() / 1000.0;
    if (elapsed_sec > 0) {
        return (bytes_transferred * 8.0) / (elapsed_sec * 1000000.0);
    }
    return 0.0;
}

} // namespace embedded_test
