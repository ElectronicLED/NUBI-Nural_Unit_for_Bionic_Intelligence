import numpy as np

# --- Rotation from RPY ---
def rpy_to_matrix(roll, pitch, yaw):
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll),  np.cos(roll)]
    ])

    Ry = np.array([
        [ np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw),  np.cos(yaw), 0],
        [0, 0, 1]
    ])

    return Rz @ Ry @ Rx


# --- URDF values ---
T1 = np.array([0.0156, 0.0151, 0.0155])
R1 = rpy_to_matrix(-0.0296, -0.0070, -0.2317)

T2 = np.array([0.0, -0.019, 0.04])
R2 = np.eye(3)

# --- Compose ---
R_total = R1 @ R2
T_total = R1 @ T2 + T1

print("Translation (base → camera):", T_total)
print("Rotation matrix:\n", R_total)
