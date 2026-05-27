import argparse
import os
import pickle
from importlib import metadata
import numpy as np
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
from nubiv6_env import NubiEnv
from action_logger import ActionLogger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="time_aware_PID")
    parser.add_argument("--ckpt", type=int, default=1600)
    parser.add_argument("--log_actions", action="store_true", help="Enable action logging")
    parser.add_argument("--max_steps", type=int, default=None, help="Maximum steps to run (None = infinite)")
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

    # Initialize action logger if enabled
    logger = None
    if args.log_actions:
        logger = ActionLogger()
        logger.start_episode(metadata={
            "exp_name": args.exp_name,
            "ckpt": args.ckpt,
            "env_cfg": str(env_cfg),
            "obs_cfg": str(obs_cfg),
            "reward_cfg": str(reward_cfg),
            "command_cfg": str(command_cfg),
        })
        print("Action logging enabled")

    max_torques = [0.0] * len(env.get_joint_torques()[0])

    # get feet link indices (names must match your URDF)
    # feet_names = ["RFoot", "LFoot"]  # replace with your actual link names
    # feet_indices = [env.robot.get_link(name).idx for name in feet_names]

    obs, _ = env.reset()
    step_count = 0

    with torch.no_grad():
        while True:
            if args.max_steps and step_count >= args.max_steps:
                print(f"Reached max steps: {args.max_steps}")
                break

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
            print("Actions:", np.rad2deg(list(actions.cpu().numpy()[0]* env_cfg["action_scale"])))
            angles_rad = list(env.dof_pos.cpu().numpy()[0])
            angles_deg = np.rad2deg(angles_rad)
            #print("Joint Angles in radians:", angles_rad)
            print("Joint Angles in degrees:", angles_deg.round(0))

            # Log step if logging is enabled (skip first step to avoid wrapped angles)
            if logger and step_count > 0:
                logger.log_step(
                    obs=obs,
                    action=actions,
                    angles=angles_deg,
                    # reward=None,  # Reward not available in eval mode
                    # done=False,
                    info={"step": step_count}
                )
            
            obs, rews, dones, infos = env.step(actions)
            step_count += 1

            if step_count % 100 == 0:
                print(f"Step: {step_count}")
            if logger and (step_count >= args.max_steps):
                print(f"Reached max steps: {args.max_steps}")
                break
            
            # print(env.get_feet_pos())
            # RLeg , LLeg = env.get_feet_height()
            # print(RLeg-LLeg)
            # links_pos = env.robot.get_links_pos()[0]
            # print(links_pos)
            
            # RFoot_pos = links_pos[12].cpu().numpy()  # shape: (num_feet, 3)
            # LFoot_pos = links_pos[13].cpu().numpy()  # shape: (num_feet, 3)
            # print(LFoot_pos,RFoot_pos)

    # Save logged episode if logging was enabled
    if logger:
        filename = f"{args.exp_name}_ckpt{args.ckpt}_steps{step_count}.pkl"
        logger.save_episode(filename)
        print(f"Episode logged with {step_count} steps")

if __name__ == "__main__":
    main()

# python3 nubiv6_eval.py -e kind_policy_fixed --ckpt 1000
# python3 nubiv6_eval.py -e kind_policy_fixed --ckpt 1000 --log_actions --max_steps 200