"""
Script to replay logged episodes on the physical robot via ROS2.
"""

import argparse
import os
import time
import numpy as np
import ast

import torch
import rclpy
from std_msgs.msg import Int16MultiArray

from action_logger import ActionReplayer
from pathlib import Path


play_Time = 35


def replay_episode_hardware(episode_path: str, action_scale: float = None, target_freq: float = 50.0):
    """Replay a logged episode on physical robot via ROS2.
    
    Args:
        episode_path: Path to the logged episode file
        action_scale: Scale factor for actions (default 1.0)
        target_freq: Publishing frequency in Hz (default 50Hz)
    """
    replayer = ActionReplayer(episode_path)
    
    print(f"\n=== Replaying Episode on Hardware ===")
    print(f"File: {episode_path}")
    print(f"Total steps: {replayer.get_total_steps()}")
    print(f"Target frequency: {target_freq} Hz")
    metadata = replayer.get_metadata()
    print(f"Metadata: {metadata}\n")

    # Determine action_scale from metadata if available
    derived_scale = None
    if isinstance(metadata, dict):
        # metadata may store env_cfg as a dict or as a string repr of a dict
        env_cfg_meta = metadata.get("env_cfg")
        if isinstance(env_cfg_meta, dict):
            derived_scale = env_cfg_meta.get("action_scale")
        elif isinstance(env_cfg_meta, str):
            try:
                parsed = ast.literal_eval(env_cfg_meta)
                if isinstance(parsed, dict):
                    derived_scale = parsed.get("action_scale")
            except Exception:
                pass
        # also allow top-level action_scale
        if derived_scale is None:
            derived_scale = metadata.get("action_scale")

    # Fallbacks
    if action_scale is None:
        action_scale = float(derived_scale) if derived_scale is not None else 1.0

    print(f"Using action_scale = {action_scale}")
    
    # Initialize ROS2
    rclpy.init()
    node = rclpy.create_node("replay_node")
    publisher_legs = node.create_publisher(Int16MultiArray, "legs_command", 10)
    
    dt = 1.0 / target_freq  # Time per step in seconds
    total_steps = replayer.get_total_steps()
    
    print(f"Publishing actions at {target_freq}Hz (dt={dt:.4f}s)")
    print(f"Total replay time: {total_steps * dt:.2f}s\n")
    
    try:
        # Wait a moment before starting
        print("Starting replay in 2 seconds...")
        time.sleep(2.0)
        
        start_time = time.time()
        
        with torch.no_grad():
            for step_idx in range(total_steps):
                step_data = replayer.get_step(step_idx)
                if step_data is None:
                    break
                
                # Get action and convert to joint positions in degrees
                action = step_data["action"].cpu().numpy()
                joints_rad = action[0] * action_scale  # shape: (num_joints,)
                joints_deg = np.rad2deg(joints_rad)
                
                # Convert to int16 and clamp to valid range
                joints_int = np.floor(joints_deg).astype(int)
                joints_int = np.clip(joints_int, -120, 120)
                
                # Publish message
                msg = Int16MultiArray()
                msg.data = [int(x) for x in joints_int]+[play_Time]
                publisher_legs.publish(msg)
                
                
                elapsed = time.time() - start_time
                expected_time = (step_idx + 1) * dt
                print(f"Step {step_idx + 1}/{total_steps} | "
                        f"Elapsed: {elapsed:.2f}s | Expected: {expected_time:.2f}s | "
                        f"Joints: {list(joints_int)}")
                
                input("Press Enter to continue to next step...")  # Step-by-step mode
                
                # Maintain desired frequency
                target_time = (step_idx + 1) * dt
                current_time = time.time() - start_time
                sleep_time = target_time - current_time
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -0.05:  # More than 50ms behind
                    print(f"  Warning: Running {-sleep_time*1000:.1f}ms behind schedule")
        
        elapsed_total = time.time() - start_time
        print(f"\nReplay completed!")
        print(f"Total time: {elapsed_total:.2f}s (expected {total_steps * dt:.2f}s)")
        
    finally:
        node.destroy_node()
        rclpy.shutdown()


def list_episodes():
    """List all available logged episodes."""
    log_dir = Path("action_logs")
    if not log_dir.exists():
        print("No action_logs directory found.")
        return []
    
    episodes = sorted(log_dir.glob("*.pkl"))
    
    if not episodes:
        print("No episodes found in action_logs/")
        return []
    
    print("\nAvailable episodes:")
    for i, ep in enumerate(episodes, 1):
        print(f"  {i}. {ep.name}")
    
    return episodes


def main():
    parser = argparse.ArgumentParser(description="Replay logged episodes on physical robot at 50Hz")
    parser.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Specific episode file to replay (from action_logs/)"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available episodes"
    )
    parser.add_argument(
        "--freq",
        type=float,
        default=50.0,
        help="Publishing frequency for hardware replay in Hz (default: 50)"
    )
    args = parser.parse_args()

    # If list flag is set, just list episodes
    if args.list:
        episodes = list_episodes()
        if episodes:
            print(f"\nTotal: {len(episodes)} episodes")
        return

    # Determine which episode to replay
    if args.file:
        episode_path = args.file
    else:
        # List all episodes and ask user to pick one
        episodes = list_episodes()
        if not episodes:
            print("No episodes to replay.")
            return
        
        choice = input(f"\nEnter episode number (1-{len(episodes)}) or filename: ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(episodes):
                episode_path = str(episodes[idx])
            else:
                print("Invalid choice")
                return
        except ValueError:
            # Assume it's a filename
            episode_path = f"action_logs/{choice}"
    
    # Check if file exists
    if not os.path.exists(episode_path):
        print(f"Episode file not found: {episode_path}")
        return

    # Replay on hardware
    replay_episode_hardware(episode_path, target_freq=args.freq)


if __name__ == "__main__":
    main()

# Usage examples:
# python3 replay_logged_episode.py -l                                                    # List available episodes
# python3 replay_logged_episode.py -f action_logs/episode_20250101_120000.pkl           # Replay on hardware at 50Hz
# python3 replay_logged_episode.py                                                       # Interactive selection (hardware at 50Hz)
# python3 replay_logged_episode.py -f action_logs/episode_20250101_120000.pkl --freq 100 # Replay on hardware at 100Hz
