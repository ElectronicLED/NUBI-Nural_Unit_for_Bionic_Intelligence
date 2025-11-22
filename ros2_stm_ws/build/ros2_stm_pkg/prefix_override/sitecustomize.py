import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/mohab/Desktop/grad_proj/ros2_stm_ws/install/ros2_stm_pkg'
