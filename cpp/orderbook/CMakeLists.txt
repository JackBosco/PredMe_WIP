cmake_minimum_required(VERSION 3.15)
project(orderbook_ext LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PYBIND11_FINDPYTHON ON)

# Try system pybind11; fallback to FetchContent
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  include(FetchContent)
  FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.13.5
  )
  FetchContent_MakeAvailable(pybind11)
endif()

pybind11_add_module(orderbook_ext
  bindings.cpp
  orderbook_core.cpp
  server_state_cpp.cpp
)

target_include_directories(orderbook_ext PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Optimize by default
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# Make sure the native module is installed into the package
install(TARGETS orderbook_ext
        LIBRARY DESTINATION .
        RUNTIME DESTINATION .
        ARCHIVE DESTINATION .)