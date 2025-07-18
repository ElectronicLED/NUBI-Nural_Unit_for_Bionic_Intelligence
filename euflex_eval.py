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

    obs, _ = env.reset()
    with torch.no_grad():
        while True:
            #print(len(EuflexEnv.get_self_collision(env)))
            actions = policy(obs)
            obs, rews, dones, infos = env.step(actions)


if __name__ == "__main__":
    main()

# python3 euflex_eval.py -e euflex-walking-collision --ckpt 300