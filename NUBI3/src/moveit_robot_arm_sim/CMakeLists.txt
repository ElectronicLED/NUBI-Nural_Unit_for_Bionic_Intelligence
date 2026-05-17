cmake_minimum_required(VERSION 3.22)
project(moveit_robot_arm_sim)

find_package(ament_cmake REQUIRED)

ament_package()
install(PROGRAMS
  scripts/move_to_xyz.py
  DESTINATION lib/${PROJECT_NAME}
)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(
    DIRECTORY launch
    DESTINATION share/${PROJECT_NAME}
    PATTERN "setup_assistant.launch" EXCLUDE)
endif()

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(FILES .setup_assistant DESTINATION share/${PROJECT_NAME})
