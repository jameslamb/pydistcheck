cmake_minimum_required(VERSION 3.10)

project(
    baseballmetrics
    LANGUAGES C CXX
)

file(GLOB SOURCES src/*.cpp)

# build individual .o files
include_directories(${PROJECT_SOURCE_DIR}/include)
add_library(
    baseballmetrics_objs OBJECT
    ${SOURCES}
)

# link those together to produce a shared library
add_library(_baseballmetrics SHARED)
target_link_libraries(
    _baseballmetrics
    PUBLIC baseballmetrics_objs
)

# link those together to produce a static library
add_library(_baseballmetrics_static STATIC)
target_link_libraries(
    _baseballmetrics_static
    PUBLIC baseballmetrics_objs
)

if(DEFINED SKBUILD)
    if(APPLE)
        set_target_properties(
            _baseballmetrics
            PROPERTIES INSTALL_RPATH "@loader_path/${CMAKE_INSTALL_LIBDIR}"
        )
    else()
        set_target_properties(
            _baseballmetrics
            PROPERTIES INSTALL_RPATH "$ORIGIN/${CMAKE_INSTALL_LIBDIR}"
        )
    endif()
else()
    # store a copy of the libraries right above the build/ folder
    set(LIBRARY_OUTPUT_PATH
        ${PROJECT_SOURCE_DIR}
    )
    set(ARCHIVE_OUTPUT_PATH
        ${PROJECT_SOURCE_DIR}
    )
endif()

# install _baseballmetrics to
install(
    TARGETS _baseballmetrics
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

# install _baseballmetrics_static to
install(
    TARGETS _baseballmetrics_static
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
