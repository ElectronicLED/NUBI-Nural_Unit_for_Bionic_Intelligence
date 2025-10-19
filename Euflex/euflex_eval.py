import argparse
import os
import pickle
from importlib import metadata

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
from euflex_env import EuflexEnv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="euflex-walking")
    parser.add_argument("--ckpt", type=int, default=100)
    args = parser.parse_args()

    gs.init()

    log_dir = f"logs/{args.exp_name}"
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(open(f"logs/{args.exp_name}/cfgs.pkl", "rb"))
    reward_cfg["reward_scales"] = {}
    print(command_cfg)

    env = EuflexEnv(
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
            obs, rews, dones, infos = env.step(actions)


if __name__ == "__main__":
    main()

# python3 euflex_eval.py -e hyper_param2 --ckpt 1000