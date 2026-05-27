import os
import json
import pickle
import numpy as np
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ActionLogger:
    """Logger for recording robot actions, observations, and episode data."""
    
    def __init__(self, log_dir: str = "action_logs"):
        """Initialize the action logger.
        
        Args:
            log_dir: Directory to store logged episodes
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.episode_data = {
            "observations": [],
            "actions": [],
            "angles": [],
            "info": [],
            "metadata": {}
        }
        self.episode_started = False
        
    def start_episode(self, metadata: Dict[str, Any] = None):
        """Start logging a new episode.
        
        Args:
            metadata: Dictionary with episode metadata (exp_name, ckpt, etc.)
        """
        self.episode_data = {
            "observations": [],
            "actions": [],
            "angles": [],
            "info": [],
            "metadata": metadata or {}
        }
        self.episode_started = True
        
    def log_step(self, obs: torch.Tensor, action: torch.Tensor, angles: np.ndarray = None, 
                 info: Dict = None):
        """Log a single step in the episode.
        
        Args:
            obs: Observation tensor
            action: Action tensor
            angles: Joint angles array (optional)
            info: Additional info dict (optional)
        """
        if not self.episode_started:
            raise RuntimeError("Episode not started. Call start_episode() first.")
        
        # Convert tensors to numpy for storage efficiency
        obs_np = obs.cpu().detach().numpy() if isinstance(obs, torch.Tensor) else np.array(obs)
        action_np = action.cpu().detach().numpy() if isinstance(action, torch.Tensor) else np.array(action)
        
        self.episode_data["observations"].append(obs_np)
        self.episode_data["actions"].append(action_np)
        
        if angles is not None:
            angles_np = angles.cpu().detach().numpy() if isinstance(angles, torch.Tensor) else np.array(angles)
            self.episode_data["angles"].append(angles_np)
        
        self.episode_data["info"].append(info or {})
        
    def save_episode(self, filename: str = None) -> str:
        """Save the current episode to disk.
        
        Args:
            filename: Custom filename (if None, uses timestamp)
            
        Returns:
            Path to saved file
        """
        if not self.episode_started or not self.episode_data["observations"]:
            raise RuntimeError("No episode data to save.")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"episode_{timestamp}.pkl"
        
        filepath = self.log_dir / filename
        
        # Convert lists to numpy arrays for efficiency
        episode_np = {
            "observations": np.array(self.episode_data["observations"]),
            "actions": np.array(self.episode_data["actions"]),
            "angles": np.array(self.episode_data["angles"]) if self.episode_data["angles"] else np.array([]),
            "metadata": self.episode_data["metadata"]
        }
        
        with open(filepath, "wb") as f:
            pickle.dump(episode_np, f)
        
        print(f"Episode saved: {filepath}")
        print(f"  Steps: {len(episode_np['observations'])}")
        print(f"  Metadata: {episode_np['metadata']}")
        
        return str(filepath)
    
    def list_episodes(self) -> List[str]:
        """List all saved episodes."""
        episodes = sorted(self.log_dir.glob("episode_*.pkl"))
        return [str(ep) for ep in episodes]


class ActionReplayer:
    """Replayer for recorded robot episodes."""
    
    def __init__(self, filepath: str):
        """Initialize the action replayer.
        
        Args:
            filepath: Path to saved episode file
        """
        with open(filepath, "rb") as f:
            self.episode_data = pickle.load(f)
        
        self.filepath = filepath
        self.current_step = 0
        self.num_steps = len(self.episode_data["observations"])
        
    def get_total_steps(self) -> int:
        """Get total number of steps in episode."""
        return self.num_steps
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get episode metadata."""
        return self.episode_data["metadata"]
    
    def reset(self):
        """Reset replayer to beginning of episode."""
        self.current_step = 0
    
    def get_step(self, step_idx: int = None) -> Dict[str, Any]:
        """Get data for a specific step.
        
        Args:
            step_idx: Step index (if None, uses current_step and increments)
            
        Returns:
            Dictionary with obs, action, angles, info for the step
        """
        if step_idx is None:
            step_idx = self.current_step
            self.current_step += 1
        
        if step_idx >= self.num_steps:
            return None
        
        return {
            "obs": torch.from_numpy(self.episode_data["observations"][step_idx]).float(),
            "action": torch.from_numpy(self.episode_data["actions"][step_idx]).float(),
            "angles": torch.from_numpy(self.episode_data["angles"][step_idx]).float() if len(self.episode_data["angles"]) > 0 else None,
            "step": step_idx,
            "total_steps": self.num_steps
        }
    
    def get_all_steps(self) -> Dict[str, Any]:
        """Get all steps at once."""
        self.reset()
        steps = []
        while self.current_step < self.num_steps:
            step = self.get_step()
            if step:
                steps.append(step)
        return steps


def create_replay_script_template(episode_path: str, output_path: str = "replay_episode.py"):
    """Create a template script for replaying a specific episode.
    
    Args:
        episode_path: Path to the episode file
        output_path: Where to save the template script
    """
    template = f'''#!/usr/bin/env python3
"""Script to replay logged episode."""

import torch
import genesis as gs
from pathlib import Path
from action_logger import ActionReplayer
from nubiv6_env import NubiEnv
import pickle
import os


def replay_episode(episode_path: str, env_cfg, obs_cfg, reward_cfg, command_cfg):
    """Replay a logged episode.
    
    Args:
        episode_path: Path to the logged episode file
        env_cfg, obs_cfg, reward_cfg, command_cfg: Environment configurations
    """
    replayer = ActionReplayer(episode_path)
    
    print(f"Replaying episode: {{episode_path}}")
    print(f"Total steps: {{replayer.get_total_steps()}}")
    print(f"Metadata: {{replayer.get_metadata()}}")
    
    # Create environment
    env = NubiEnv(
        num_envs=1,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=True,
    )
    
    # Get initial observation for verification
    obs_initial = replayer.episode_data["observations"][0]
    
    # Reset environment to initial state
    obs, _ = env.reset()
    
    with torch.no_grad():
        for step_idx in range(replayer.get_total_steps()):
            step_data = replayer.get_step(step_idx)
            if step_data is None:
                break
            
            action = step_data["action"]
            obs, reward, done, info = env.step(action)
            
            if (step_idx + 1) % 100 == 0:
                print(f"Step {{step_idx + 1}}/{{replayer.get_total_steps()}}")
            
            if done:
                print(f"Episode finished at step {{step_idx + 1}}")
                break


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="substep_fall20_default006_rep")
    args = parser.parse_args()
    
    gs.init()
    
    # Load environment configurations
    log_dir = f"logs/{{args.exp_name}}"
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
        open(f"logs/{{args.exp_name}}/cfgs.pkl", "rb")
    )
    reward_cfg["reward_scales"] = {{}}
    
    # Replay the episode
    replay_episode("{episode_path}", env_cfg, obs_cfg, reward_cfg, command_cfg)
'''
    
    with open(output_path, "w") as f:
        f.write(template)
    
    print(f"Replay template created: {output_path}")
