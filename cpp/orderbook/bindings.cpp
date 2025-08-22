#include "server_state_cpp.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "orderbook_core.hpp"

namespace py = pybind11;

PYBIND11_MODULE(orderbook_ext, m) {
    m.doc() = "OrderBook C++ core (pybind11, C++11)";

    py::class_<LOBEntry>(m, "LOBEntry")
        .def(py::init<double,double>())
        .def_readwrite("price", &LOBEntry::price)
        .def_readwrite("quantity", &LOBEntry::quantity);

    py::class_<Trade>(m, "Trade")
        .def(py::init<double,double>())
        .def_readwrite("price", &Trade::price)
        .def_readwrite("quantity", &Trade::quantity);

    py::class_<OrderBookCore>(m, "OrderBookCore")
        .def(py::init<double,const std::vector<LOBEntry>&,const std::vector<LOBEntry>&>(),
             py::arg("tick_size"),
             py::arg("bids"),
             py::arg("offers"))
        .def("set_tick_size", &OrderBookCore::set_tick_size)
        .def("best_bid", [](const OrderBookCore& ob) -> py::object {
            double p=0.0,q=0.0;
            if (ob.best_bid(p,q)) return py::make_tuple(p,q);
            return py::none();
        })
        .def("best_offer", [](const OrderBookCore& ob) -> py::object {
            double p=0.0,q=0.0;
            if (ob.best_offer(p,q)) return py::make_tuple(p,q);
            return py::none();
        })
        .def("update_level", &OrderBookCore::update_level, py::arg("entry"), py::arg("side"), py::arg("is_delta")=false)
        .def("update_levels", &OrderBookCore::update_levels, py::arg("entries"), py::arg("side"), py::arg("is_delta")=false)
        .def("add_limit_order", &OrderBookCore::add_limit_order)
        .def("get_col", &OrderBookCore::get_col);

    py::class_<ServerStateCPP>(m, "ServerState")
        .def(py::init<>())
        .def("init_order_book", &ServerStateCPP::init_order_book,
             py::arg("exchange_id"), py::arg("market_id"),
             py::arg("bids"), py::arg("offers"))
        .def("update_order_book", (void (ServerStateCPP::*)(const std::string&, const std::string&, char, char, const LOBEntry&, bool)) &ServerStateCPP::update_order_book,
             py::arg("exchange_id"), py::arg("market_id"), py::arg("pred"), py::arg("side"), py::arg("data"), py::arg("is_delta") = false)
        .def("update_order_book", (void (ServerStateCPP::*)(const std::string&, const std::string&, char, char, const std::vector<LOBEntry>&, bool)) &ServerStateCPP::update_order_book,
             py::arg("exchange_id"), py::arg("market_id"), py::arg("pred"), py::arg("side"), py::arg("data"), py::arg("is_delta") = false)
        .def("get_market", &ServerStateCPP::get_market,
             py::arg("exchange_id"), py::arg("market_id"))
        .def("set_tick_size", &ServerStateCPP::set_tick_size,
             py::arg("exchange_id"), py::arg("market_id"), py::arg("new_tick_size"));
}