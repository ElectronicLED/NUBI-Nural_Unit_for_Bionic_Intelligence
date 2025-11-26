import depthai as dai

device = dai.Device()
calib = device.readCalibration()

left_intrinsics = calib.getCameraIntrinsics(dai.CameraBoardSocket.LEFT)
right_intrinsics = calib.getCameraIntrinsics(dai.CameraBoardSocket.RIGHT)

print("Left:", left_intrinsics)
print("Right:", right_intrinsics)
