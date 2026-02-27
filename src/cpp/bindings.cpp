/**================================================================================
* FILE: bindings.cpp

* Purpose:
* 1. Implementation of high-performance DUT communication
 
* Author: Diksha Ravindran
* Year: Jan - 2026
* version: Not completed yet - Draft 
================================================================================
*/

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include "fast_comms.h"

namespace py = pybind11;
using namespace embedded_test;

PYBIND11_MODULE(fast_comms_cpp, m) {
    m.doc() = "High-performance C++ communication module for embedded device testing";
    
    // PacketStats structure
    py::class_<PacketStats>(m, "PacketStats")
        .def(py::init<>())
        .def_readwrite("packets_sent", &PacketStats::packets_sent)
        .def_readwrite("packets_received", &PacketStats::packets_received)
        .def_readwrite("bytes_sent", &PacketStats::bytes_sent)
        .def_readwrite("bytes_received", &PacketStats::bytes_received)
        .def_readwrite("errors", &PacketStats::errors)
        .def_readwrite("avg_latency_us", &PacketStats::avg_latency_us)
        .def("__repr__", [](const PacketStats& stats) {
            return "<PacketStats sent=" + std::to_string(stats.packets_sent) +
                   " received=" + std::to_string(stats.packets_received) +
                   " errors=" + std::to_string(stats.errors) + ">";
        });
    
    // CommResult structure
    py::class_<CommResult>(m, "CommResult")
        .def(py::init<>())
        .def_readwrite("success", &CommResult::success)
        .def_readwrite("data", &CommResult::data)
        .def_readwrite("latency_us", &CommResult::latency_us)
        .def_readwrite("error_message", &CommResult::error_message)
        .def("__repr__", [](const CommResult& result) {
            return "<CommResult success=" + std::string(result.success ? "True" : "False") +
                   " latency=" + std::to_string(result.latency_us) + "us>";
        });
    
    // FastComms class
    py::class_<FastComms>(m, "FastComms")
        .def(py::init<const std::string&, uint32_t>(),
             py::arg("interface_name"),
             py::arg("timeout_ms") = 1000,
             "Create FastComms instance\n\n"
             "Args:\n"
             "    interface_name: Network interface (e.g., 'eth0')\n"
             "    timeout_ms: Timeout in milliseconds (default: 1000)")
        
        .def("initialize", &FastComms::initialize,
             "Initialize the communication channel\n\n"
             "Returns:\n"
             "    bool: True if successful")
        
        .def("close", &FastComms::close,
             "Close the communication channel")
        
        .def("send_packet", &FastComms::send_packet,
             py::arg("data"),
             "Send raw packet\n\n"
             "Args:\n"
             "    data: Packet data as bytes\n\n"
             "Returns:\n"
             "    bool: True if sent successfully")
        
        .def("receive_packet", 
             [](FastComms& self, size_t max_size) {
                 std::vector<uint8_t> buffer;
                 int result = self.receive_packet(buffer, max_size);
                 return py::make_tuple(result, buffer);
             },
             py::arg("max_size") = 4096,
             "Receive raw packet with timeout\n\n"
             "Args:\n"
             "    max_size: Maximum size to receive\n\n"
             "Returns:\n"
             "    tuple: (bytes_received, data)")
        
        .def("send_and_receive",
             [](FastComms& self, const std::vector<uint8_t>& request) {
                 std::vector<uint8_t> response;
                 CommResult result = self.send_and_receive(request, response);
                 return result;
             },
             py::arg("request"),
             "Send packet and wait for response\n\n"
             "Args:\n"
             "    request: Request data\n\n"
             "Returns:\n"
             "    CommResult: Result with response data and latency")
        
        .def("burst_send", &FastComms::burst_send,
             py::arg("packets"),
             "Burst send multiple packets\n\n"
             "Args:\n"
             "    packets: List of packet data\n\n"
             "Returns:\n"
             "    int: Number of packets successfully sent")
        
        .def("measure_latency", &FastComms::measure_latency,
             py::arg("payload"),
             "Measure round-trip latency\n\n"
             "Args:\n"
             "    payload: Ping payload\n\n"
             "Returns:\n"
             "    int: Latency in microseconds, -1 on error")
        
        .def("stress_test", &FastComms::stress_test,
             py::arg("duration_ms"),
             py::arg("packet_size") = 64,
             "Stress test - send packets at maximum rate\n\n"
             "Args:\n"
             "    duration_ms: Duration in milliseconds\n"
             "    packet_size: Size of each packet\n\n"
             "Returns:\n"
             "    PacketStats: Statistics about the stress test")
        
        .def("get_statistics", &FastComms::get_statistics,
             "Get communication statistics\n\n"
             "Returns:\n"
             "    PacketStats: Current statistics")
        
        .def("reset_statistics", &FastComms::reset_statistics,
             "Reset statistics counters")
        
        .def("set_timeout", &FastComms::set_timeout,
             py::arg("timeout_ms"),
             "Set timeout\n\n"
             "Args:\n"
             "    timeout_ms: Timeout in milliseconds")
        
        .def("is_ready", &FastComms::is_ready,
             "Check if interface is ready\n\n"
             "Returns:\n"
             "    bool: True if ready for communication")
        
        .def("__enter__", [](FastComms& self) -> FastComms& {
            self.initialize();
            return self;
        })
        
        .def("__exit__", [](FastComms& self, py::object, py::object, py::object) {
            self.close();
        });
    
    // PacketValidator class
    py::class_<PacketValidator>(m, "PacketValidator")
        .def_static("calculate_crc32", &PacketValidator::calculate_crc32,
                   py::arg("data"),
                   "Calculate CRC32 checksum\n\n"
                   "Args:\n"
                   "    data: Data to checksum\n\n"
                   "Returns:\n"
                   "    int: CRC32 value")
        
        .def_static("verify_packet", &PacketValidator::verify_packet,
                   py::arg("packet"),
                   py::arg("expected_crc"),
                   "Verify packet integrity\n\n"
                   "Args:\n"
                   "    packet: Packet data\n"
                   "    expected_crc: Expected CRC value\n\n"
                   "Returns:\n"
                   "    bool: True if valid")
        
        .def_static("calculate_simple_checksum", &PacketValidator::calculate_simple_checksum,
                   py::arg("data"),
                   "Calculate simple checksum\n\n"
                   "Args:\n"
                   "    data: Data to checksum\n\n"
                   "Returns:\n"
                   "    int: Checksum value");
    
    // PerformanceMonitor class
    py::class_<PerformanceMonitor>(m, "PerformanceMonitor")
        .def(py::init<>())
        .def("start_measurement", &PerformanceMonitor::start_measurement,
             "Start timing measurement")
        .def("stop_measurement", &PerformanceMonitor::stop_measurement,
             "Stop timing measurement")
        .def("get_elapsed_ms", &PerformanceMonitor::get_elapsed_ms,
             "Get elapsed time in milliseconds")
        .def("get_throughput_mbps", &PerformanceMonitor::get_throughput_mbps,
             py::arg("bytes_transferred"),
             "Calculate throughput in Mbps");
}
