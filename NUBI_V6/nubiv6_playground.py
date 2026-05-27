import numpy as np
import genesis as gs
import torch
import time
from nubiv6_env import NubiEnv
from pynput.keyboard import Key, Listener
from nubiv6_train import get_cfgs
import rclpy
from std_msgs.msg import Int16MultiArray

rclpy.init()
node = rclpy.create_node("RL_NODE")
publisher_legs = node.create_publisher(Int16MultiArray,"legs_command",10)

def legs_command(arr):
    msg = Int16MultiArray()
    # Ensure values are Python ints (not numpy types) and within int16 bounds
    try:
        data = [int(x) for x in arr]
    except Exception:
        # Fallback: try to convert the whole object to a flat list first
        data = [int(x) for x in list(np.asarray(arr).reshape(-1))]
    # clamp to int16 range
    data = [max(-120, min(120, x)) for x in data]
    msg.data = data
    publisher_legs.publish(msg)





# Initialize Genesis
gs.init()

# Load configs
env_cfg, obs_cfg, reward_cfg, command_cfg = get_cfgs()

env_cfg["base_init_pos"] = [0.0, 0.0, 0.4]
# Set gravity before creating the environment
env_cfg["gravity"] = (0.0, 0.0, 0.0) 




actions1 = torch.tensor([[0.0] * 12], device=gs.device) 
actions2 = torch.tensor([[
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # Right leg joints
    0.0, 0.0, 0.0, 0.0, 0.0, 0.7854   # Left leg joints
]], device=gs.device) * (1/env_cfg["action_scale"])  # Example action for 12 joints

[8, 29, 7, -15, 2, 17, -6, -2, 16, 1, 23, -3]


action = actions1

def on_press(key):
    global action

    print(f"\n\n############################ Key pressed: {key}\n\n")
    if key == Key.space:
        action = actions2
    else:
        action = actions1



# Create environment
env = NubiEnv(
    num_envs=1,
    env_cfg=env_cfg,
    obs_cfg=obs_cfg,
    reward_cfg=reward_cfg,
    command_cfg=command_cfg,
    show_viewer=True,
)

listener = Listener(on_press=on_press)
listener.start() 

# Reset environment
obs, _ = env.reset()

cmd_sent = False
start_sim_time = 0.0
target_angle_rad = 1.57 # 90 degrees

simtime = 0.0
realtime = time.time()

while True:
    
    print("Sim time: ", simtime)
    print("Real time:", time.time()-realtime, "\n")

    print("Joint positions: \n")
    print(np.rad2deg(env.dof_pos[0].cpu().numpy())[0:6])
    print(np.rad2deg(env.dof_pos[0].cpu().numpy())[6:], "\n##############################")
    # if torch.allclose(env.dof_pos[0], actions2[0]):
    #     print("\n\nend position reached\n")
    #     exit()

    legs_pos_cmd = action


    obs, rew, done, info = env.step(action)
    simtime += env.dt


    legs_pos_cmd = np.rad2deg(action.cpu().numpy()* env_cfg["action_scale"])
    legs_pos_cmd = np.floor(legs_pos_cmd).astype(int)
    legs_command(list(legs_pos_cmd[0]))


    # 2. Check current joint position
    current_angle = env.dof_pos[0].cpu().numpy()[9] # Left knee index based on your script
    
    # 3. Detect when you press spacebar to trigger the action
    if torch.equal(action, actions2) and not cmd_sent:
        cmd_sent = True
        start_sim_time = simtime
        start_real_time = time.time()
        print(f"\n[COMMAND SENT] Target: 90 deg. Sim time: {start_sim_time:.3f}s")
        
    # 4. Detect when the joint actually crosses the target
    if cmd_sent and current_angle >= (target_angle_rad * 0.95): # Reached 95% of target
        end_sim_time = simtime
        end_real_time = time.time()
        sim_time_to_reach = end_sim_time - start_sim_time
        real_time_to_reach = end_real_time - start_real_time
        print(f"[TARGET REACHED] It took {sim_time_to_reach:.3f} seconds of simulation time!")
        print(f"[TARGET REACHED] It took {real_time_to_reach:.3f} seconds of real time!")
        cmd_sent = False # Reset for the next test
        exit()
    
    
    #print(f"Obs: {obs}")
    #print(f"Reward: {rew}")
    #print(f"Done: {done}")