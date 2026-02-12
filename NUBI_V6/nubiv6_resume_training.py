import argparse
import os
import pickle
import shutil
from importlib import metadata

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



parser = argparse.ArgumentParser()
parser.add_argument("-e", "--exp_name", type=str, default="time_aware_replicate")
parser.add_argument("-B", "--num_envs", type=int, default=4096)# default was 4096
parser.add_argument("--max_iterations", type=int, default=501)
args = parser.parse_args()

gs.init(logging_level="warning")

log_dir = f"logs/{args.exp_name}"
resume_path = None

# Check if we should resume training
if os.path.exists(log_dir):
    # Find the latest checkpoint
    checkpoints = [f for f in os.listdir(log_dir) if f.startswith("model_") and f.endswith(".pt")]
    if checkpoints:
        # Sort by iteration number to find the latest
        checkpoints.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))
        resume_path = os.path.join(log_dir, checkpoints[-1])
        print(f"Resuming training from: {resume_path}")

env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(open(f"logs/{args.exp_name}/cfgs.pkl", "rb"))

command_cfg["lin_vel_y_range"] = [-0.1, 0.1]
command_cfg["lin_vel_x_range"] = [0.0,0.0]
#train_cfg["entropy_coef"] = 0.005# Decrease exploration rate
train_cfg["learning_rate"] = 2e-4  # Adjust learning rate if needed
train_cfg["schedule"] = "none"  # Use linear learning rate decay

# Only remove the log directory if we are not resuming
if not resume_path:
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
os.makedirs(log_dir, exist_ok=True)

env = NubiEnv(
    num_envs=args.num_envs, env_cfg=env_cfg, obs_cfg=obs_cfg, reward_cfg=reward_cfg, command_cfg=command_cfg
    )

runner = OnPolicyRunner(env, train_cfg, log_dir, device=gs.device)

if resume_path:
    runner.load(resume_path)

runner.learn(num_learning_iterations=args.max_iterations, init_at_random_ep_len=True)

# python3 nubiv6_resume_training.py --exp_name first_try --max_iterations 501