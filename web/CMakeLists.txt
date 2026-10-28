cmake_minimum_required(VERSION 3.20)
project(slipstream_web_witness LANGUAGES CXX)
if(NOT EMSCRIPTEN)
  message(FATAL_ERROR "Configure with emcmake; desktop build remains scripts/setup.sh")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include(FetchContent)
set(MSDFGEN_CORE_ONLY ON CACHE BOOL "" FORCE)
set(MSDFGEN_USE_SKIA OFF CACHE BOOL "" FORCE)
set(MSDFGEN_INSTALL OFF CACHE BOOL "" FORCE)
FetchContent_Declare(msdfgen
  GIT_REPOSITORY https://github.com/Chlumsky/msdfgen.git
  GIT_TAG e06c7eaaaa071445ec77a1d73f942889f796b70b)
FetchContent_MakeAvailable(msdfgen)
set(NATIVE "${SLIPSTREAM_SOURCE}/native")
add_library(slipstream_web STATIC
  ${NATIVE}/atlas.cpp ${NATIVE}/shapes.cpp ${NATIVE}/mesh.cpp
  ${NATIVE}/path.cpp ${NATIVE}/canvas.cpp ${NATIVE}/freetype.cpp
  ${NATIVE}/advanced_shaders.cpp ${NATIVE}/paint.cpp
  ${NATIVE}/compositor.cpp ${NATIVE}/reactive_renderer.cpp
  ${SLUGHORN_SOURCE}/slughorn/slughorn.cpp)
target_include_directories(slipstream_web PUBLIC ${NATIVE}
  ${SLUGHORN_SOURCE} ${SLUGHORN_SOURCE}/ext/json/include
  ${msdfgen_SOURCE_DIR})
target_compile_definitions(slipstream_web PRIVATE SLUGHORN_HAS_SDF GLFW_INCLUDE_ES3)
target_compile_options(slipstream_web PUBLIC -fexceptions -sUSE_FREETYPE=1)
target_link_libraries(slipstream_web PRIVATE msdfgen-core)
add_executable(witness witness.cpp)
target_link_libraries(witness PRIVATE slipstream_web)
target_include_directories(witness PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/..")
target_link_options(witness PRIVATE -fexceptions -sUSE_FREETYPE=1 -sUSE_GLFW=3
  -sMIN_WEBGL_VERSION=2 -sMAX_WEBGL_VERSION=2 -sALLOW_MEMORY_GROWTH=1
  -sASSERTIONS=1 --preload-file "${WEB_FONT}@/font.ttf"
  --shell-file "${CMAKE_CURRENT_SOURCE_DIR}/shell.html")
set_target_properties(witness PROPERTIES SUFFIX ".html")
add_library(slipstream_web_scene STATIC witness.cpp)
target_compile_definitions(slipstream_web_scene PRIVATE WEB_JOLT_HOST)
target_include_directories(slipstream_web_scene PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/..")
target_link_libraries(slipstream_web_scene PRIVATE slipstream_web)
