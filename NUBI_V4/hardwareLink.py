import argparse
import os
import pickle
from importlib import metadata
import numpy as np
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

import torch

try:
    try:
        if metadata.version("rsl-rl"):
            raise ImportError
    except metadata.PackageNotFoundError:
        if metadata.version("rsl-rl-lib") != "2.2.4":
            raise ImportError
except (metadata.PackageNotFoundError, ImportError) as e:
    raise ImportError("Please uninstall 'rsl_rl' and install 'rsl-rl-lib==2.2.4'.") from e
from rsl_rl.runners import OnPolicyRunner

import genesis as gs
from nubiv4_env import NubiEnv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="time_aware_P254_D25")
    parser.add_argument("--ckpt", type=int, default=900)
    args = parser.parse_args()

    gs.init()

    log_dir = f"logs/{args.exp_name}"
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(open(f"logs/{args.exp_name}/cfgs.pkl", "rb"))
    reward_cfg["reward_scales"] = {}
    print(command_cfg)

    env = NubiEnv(
        num_envs=1,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=True,
    )

    runner = OnPolicyRunner(env, train_cfg, log_dir, device=gs.device)
    resume_path = os.path.join(log_dir, f"model_{args.ckpt}.pt")
    runner.load(resume_path)
    policy = runner.get_inference_policy(device=gs.device)


    max_torques = [0.0] * len(env.get_joint_torques()[0])

    # get feet link indices (names must match your URDF)
    # feet_names = ["RFoot", "LFoot"]  # replace with your actual link names
    # feet_indices = [env.robot.get_link(name).idx for name in feet_names]


    obs, _ = env.reset()
    with torch.no_grad():
        while True:
            # env.commands[0, 0] = 0.0  # Forward velocity
            # env.commands[0, 1] = 0.0  # Lateral velocity
            # env.commands[0, 2] = 0.0  # Yaw rate
            #print(len(EuflexEnv.get_self_collision(env)))
            torques = env.get_joint_torques()
            for x in range(len(max_torques)):
                if abs(torques[0][x].item()) > abs(max_torques[x]):
                    max_torques[x] = torques[0][x].item()

            # print(" RHip yaw:",max_torques[0],"\t","LHip yaw:",max_torques[6],"\n",
            #       "RHip roll:", max_torques[1],"\t","LHip roll:",max_torques[7],"\n",
            #       "RHip pitchl:", max_torques[2],"\t","LHip pitch:",max_torques[8],"\n",
            #       "RKnee pitch:", max_torques[3],"\t","LKnee pitch:",max_torques[9],"\n",
            #       "RAnkle roll:", max_torques[4],"\t","LAnkle roll:",max_torques[10],"\n",
            #       "RAnkle pitch:", max_torques[5],"\t","LAnkle pitch:",max_torques[11],"\n",)
            
            
            actions = policy(obs)
            legs_pos_cmd = np.rad2deg(actions.cpu().numpy())
            legs_pos_cmd = np.floor(legs_pos_cmd).astype(int)

            print("Actions:", list(legs_pos_cmd[0]))
            legs_command(list(legs_pos_cmd[0]))

            #input("Press Enter to step.. ")
            obs, rews, dones, infos = env.step(actions)
            
            # print(env.get_feet_pos())
            # RLeg , LLeg = env.get_feet_height()
            # print(RLeg-LLeg)
            # links_pos = env.robot.get_links_pos()[0]
            # print(links_pos)
            
            # RFoot_pos = links_pos[12].cpu().numpy()  # shape: (num_feet, 3)
            # LFoot_pos = links_pos[13].cpu().numpy()  # shape: (num_feet, 3)
            # print(LFoot_pos,RFoot_pos)


if __name__ == "__main__":
    main()

# python3 nubiv4_eval.py -e first_try --ckpt 900