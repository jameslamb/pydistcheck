cmake_minimum_required(VERSION 3.10)

project(
    baseballmetrics
    LANGUAGES C CXX
)

file(GLOB SOURCES src/*.cpp)

# build individual .o files
include_directories(${PROJECT_SOURCE_DIR}/include)
add_library(
    baseballmetrics_objs
    OBJECT ${SOURCES}
)

# link those together to produce a library
add_library(_baseballmetrics SHARED)
target_link_libraries(_baseballmetrics PUBLIC baseballmetrics_objs)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")

if(DEFINED SKBUILD)
    if(APPLE)
      set_target_properties(
        _baseballmetrics PROPERTIES INSTALL_RPATH "@loader_path/${CMAKE_INSTALL_LIBDIR}"
      )
    else()
      set_target_properties(
        _baseballmetrics PROPERTIES INSTALL_RPATH "$ORIGIN/${CMAKE_INSTALL_LIBDIR}"
      )
    endif()
else()
    # store a copy of the library right about the build/ folder
    set(LIBRARY_OUTPUT_PATH ${PROJECT_SOURCE_DIR})
endif()

# ensure that the library is a .so on mac
set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")

# install lib_baseballmetrics to 
install(
  TARGETS _baseballmetrics
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
