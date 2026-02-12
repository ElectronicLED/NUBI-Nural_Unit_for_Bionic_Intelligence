import genesis as gs
from nubiv6_env import NubiEnv

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




def get_train_cfg(exp_name, max_iterations):
    train_cfg_dict = {
        "algorithm": {
            "class_name": "PPO",
            "clip_param": 0.2,
            "desired_kl": 0.01,
            "entropy_coef": 0.01,
            "gamma": 0.99,
            "lam": 0.95,
            "learning_rate": 0.001, # Can start slightly higher with a schedule
            "max_grad_norm": 1.0,
            "num_learning_epochs": 5,
            "num_mini_batches": 4,
            "schedule": "adaptive", # Changed from "adaptive" to "linear" for explicit decay could be "constant" or "none"
            "use_clipped_value_loss": True,
            "value_loss_coef": 1.0,
        },
        "init_member_classes": {},
        "policy": {
            "activation": "elu",
            "actor_hidden_dims": [512, 256, 128],
            "critic_hidden_dims": [512, 256, 128],
            "init_noise_std": 1.0,
            "class_name": "ActorCritic",
        },
        "runner": {
            "checkpoint": -1,
            "experiment_name": exp_name,
            "load_run": -1,
            "log_interval": 1,
            "max_iterations": max_iterations,
            "record_interval": -1,
            "resume": False,
            "resume_path": None,
            "run_name": "",
        },
        "runner_class_name": "OnPolicyRunner",
        "num_steps_per_env": 24, # Increased from 24 standard is 1024
        "save_interval": 100,
        "empirical_normalization": None,
        "seed": 1,
    }

    return train_cfg_dict


def get_cfgs():
    env_cfg = {
        "num_actions": 12,
        # joint/link names
        "default_joint_angles": {  # [rad]
            # --- LEGS: Spread hips to stop LTibia <--> RFemur collision ---
            "RHip_roll": 0.0,    # Move Right leg out
            "LHip_roll": 0.0,     # Move Left leg out
            
            # --- ARMS: Lift arms to stop chest <--> LForearm collision ---
            "RShoulder_pitch": 0, # Adjust based on your joint zero-point
            "LShoulder_pitch": 0, # Adjust based on your joint zero-point
            "RShoulder_roll": 0, # Lift arm away from body
            "LShoulder_roll": 0,  # Lift arm away from body
            
            # --- KEEP OTHERS AT 0.0 ---
            "RHip_yaw": 0.0,
            "RHip_pitch": 0.0,
            "RKnee_pitch": 0.0,
            "RAnkle_roll": 0.0,
            "RAnkle_pitch": 0.0,

            "LHip_yaw": 0.0,
            "LHip_pitch": 0.0,
            "LKnee_pitch": 0.0,
            "LAnkle_roll": 0.0,
            "LAnkle_pitch": 0.0,
        },
        "joint_names": [
            'RHip_yaw',
            'RHip_roll',
            'RHip_pitch',
            'RKnee_pitch',
            'RAnkle_roll',
            'RAnkle_pitch',

            'LHip_yaw',
            'LHip_roll',
            'LHip_pitch',
            'LKnee_pitch',
            'LAnkle_roll',
            'LAnkle_pitch'
        ],
        # PD
        "kp": 254.0,
        "kd": 15.0,
        # termination
        "termination_if_roll_greater_than": 10,  # degree
        "termination_if_pitch_greater_than": 10,
        # base pose
        "base_init_pos": [0.0, 0.0, 0.23],
        "base_init_quat": [0.0, 0.0, 0.0, 1.0],  # 90 degrees about z-axis
        "episode_length_s": 20.0,
        "resampling_time_s": 4.0,
        "action_scale": 0.25,
        "simulate_action_latency": True,
        "clip_actions": 100.0,
    }
    obs_cfg = {
        "num_obs": 46,# originally was 46
        "obs_scales": {
            "lin_vel": 2.0,
            "ang_vel": 0.25,
            #"euler_angles": 0.5,
            "dof_pos": 1.0,
            "dof_vel": 0.05,
            "time": 1.0,
        },
    }
    reward_cfg = {
        "tracking_sigma": 0.25,
        "base_height_target": 0.2,
        "feet_height_target_difference": 0.025,
        "reward_scales": {
            "tracking_lin_vel": 1.0,
            "tracking_ang_vel": 0.2,
            "lin_vel_z": -1.0,
            "base_height": -50.0,
            "action_rate": -0.005,
            "similar_to_default": -0.1,
            "collision": -0.5, # Penalize collisions this number needs tuning
            #"feet_height_alternate": 1.3
        },
    }
    command_cfg = {
        "num_commands": 3,
        "lin_vel_x_range": [0.3, 0.3],
        "lin_vel_y_range": [0.0, 0.0],
        "ang_vel_range": [0, 0],
    }

    return env_cfg, obs_cfg, reward_cfg, command_cfg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="first_try")
    parser.add_argument("-B", "--num_envs", type=int, default=4096)# default was 4096
    parser.add_argument("--max_iterations", type=int, default=101)
    args = parser.parse_args()

    gs.init(logging_level="warning")

    log_dir = f"logs/{args.exp_name}"
    env_cfg, obs_cfg, reward_cfg, command_cfg = get_cfgs()
    train_cfg = get_train_cfg(args.exp_name, args.max_iterations)

    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    pickle.dump(
        [env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg],
        open(f"{log_dir}/cfgs.pkl", "wb"),
    )

    env = NubiEnv(
        num_envs=args.num_envs, env_cfg=env_cfg, obs_cfg=obs_cfg, reward_cfg=reward_cfg, command_cfg=command_cfg
    )

    runner = OnPolicyRunner(env, train_cfg, log_dir, device=gs.device)

    runner.learn(num_learning_iterations=args.max_iterations, init_at_random_ep_len=True)


if __name__ == "__main__":
    main()


# python3 nubiv4_train.py --exp_name time_aware_PID --max_iterations 1001
# tensorboard --logdir logs