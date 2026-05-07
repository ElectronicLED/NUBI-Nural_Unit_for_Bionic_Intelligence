# Action Logging & Replay System

A complete system for logging robot actions during evaluation and replaying them on the physical robot.

## Overview

The system consists of three main components:

1. **action_logger.py** - Core logging and replay classes
2. **nubiv6_eval.py** - Main evaluation script with optional logging (use `--log_actions` flag)
3. **replay_logged_episode.py** - Script to replay logged episodes on physical robot via ROS2

## Quick Start

### 1. Log an Episode

Log actions from the main evaluation script using the `--log_actions` flag:

```bash
python3 nubiv6_eval.py -e time_aware_PID --ckpt 1600 --log_actions --max_steps 2000
```

This will:
- Run the policy for 5000 steps (or indefinitely if `--max_steps` not set)
- Log every observation and action
- Save to `action_logs/time_aware_PID_ckpt1600_steps5000.pkl`

### 2. List Logged Episodes

View all your logged episodes:

```bash
python3 replay_logged_episode.py -l
```

Output:
```
Available episodes:
  1. time_aware_PID_ckpt1600_steps5000.pkl
  2. trapezoidel_200ms_ckpt200_steps2000.pkl
  3. substep_fall20_default006_rep_ckpt800_steps5000.pkl

Total: 3 episodes
```

### 3. Replay an Episode

Replay on the physical robot at 50Hz:

```bash
# Interactive selection (hardware at 50Hz)
python3 replay_logged_episode.py

# Specific file at 50Hz
python3 replay_logged_episode.py -f action_logs/time_aware_PID_ckpt1600_steps5000.pkl

# Custom frequency (e.g., 100Hz)
python3 replay_logged_episode.py -f action_logs/time_aware_PID_ckpt1600_steps5000.pkl --freq 100
```

Hardware replay will:
- Publish actions to the `legs_command` ROS2 topic
- Convert actions to joint positions in degrees
- Maintain the specified frequency (default 50Hz)
- Show real-time progress and timing information

## Usage Examples

### Standard Evaluation Without Logging

```bash
python3 nubiv6_eval.py -e time_aware_PID --ckpt 1600
```

### Evaluation With Logging and Limited Steps

```bash
python3 nubiv6_eval.py -e trapezoidel_200ms --ckpt 500 --log_actions --max_steps 2000
```

### Replay Logged Episode on Robot

```bash
# List all logged episodes
python3 replay_logged_episode.py -l

# Replay a specific episode
python3 replay_logged_episode.py -f action_logs/time_aware_PID_ckpt1600_steps5000.pkl

# Replay at custom frequency
python3 replay_logged_episode.py -f action_logs/time_aware_PID_ckpt1600_steps5000.pkl --freq 100
```

### Analyze Logged Data

```python
from action_logger import ActionReplayer
import torch

replayer = ActionReplayer("action_logs/time_aware_PID_ckpt1600_steps5000.pkl")

# Get metadata
print(f"Experiment: {replayer.get_metadata()}")
print(f"Total steps: {replayer.get_total_steps()}")

# Loop through steps
replayer.reset()
for i in range(replayer.get_total_steps()):
    step = replayer.get_step()
    obs = step["obs"]           # observation tensor
    action = step["action"]     # action tensor
    done = step["done"]         # episode done flag
    if i % 100 == 0:
        print(f"Step {i}: action shape = {action.shape}")
```

### Extract Data for Processing

```python
from action_logger import ActionReplayer
import numpy as np

replayer = ActionReplayer("action_logs/time_aware_PID_ckpt1600_steps5000.pkl")

# Get numpy arrays directly
obs = replayer.episode_data["observations"]  # shape: (steps, obs_dim)
actions = replayer.episode_data["actions"]   # shape: (steps, action_dim)
metadata = replayer.get_metadata()

print(f"Episode: {metadata['exp_name']}")
print(f"Recorded {len(obs)} steps")
print(f"Action shape: {actions.shape}")
print(f"Mean action: {np.mean(actions, axis=0)}")
print(f"Min action: {np.min(actions, axis=0)}")
print(f"Max action: {np.max(actions, axis=0)}")
```

## File Format

Episodes are saved as pickle files containing:

```python
{
    "observations": np.ndarray (shape: [num_steps, obs_dim]),
    "actions": np.ndarray (shape: [num_steps, action_dim]),
    "rewards": np.ndarray (shape: [num_steps] or [0] if not available),
    "dones": np.ndarray (shape: [num_steps], dtype=bool),
    "metadata": dict with experiment info
}
```

## Logging to Your Own Scripts

To add logging to any evaluation script:

```python
from action_logger import ActionLogger
import torch

# Create logger
logger = ActionLogger()
logger.start_episode(metadata={"exp_name": "my_test"})

# In your simulation loop
with torch.no_grad():
    obs, _ = env.reset()
    for step in range(max_steps):
        actions = policy(obs)
        
        # Log the step
        logger.log_step(obs, actions)
        
        # Step environment
        obs, reward, done, info = env.step(actions)

# Save when done
logger.save_episode(f"my_experiment_steps{step}.pkl")
```

## Command-Line Arguments

### nubiv6_eval.py

```
usage: nubiv6_eval.py [-h] [-e EXP_NAME] [--ckpt CKPT] [--log_actions] [--max_steps MAX_STEPS]

options:
  -h, --help            Show help message
  -e, --exp_name        Experiment name (default: time_aware_PID)
  --ckpt                Checkpoint number (default: 1600)
  --log_actions         Enable action logging to action_logs/
  --max_steps           Maximum steps to run (None = infinite)
```

**Examples:**
```bash
# Evaluate without logging
python3 nubiv6_eval.py -e trapezoidel_200ms --ckpt 500

# Evaluate with logging for 2000 steps
python3 nubiv6_eval.py -e trapezoidel_200ms --ckpt 500 --log_actions --max_steps 2000
```

### replay_logged_episode.py

```
usage: replay_logged_episode.py [-h] [-f FILE] [-l] [--freq FREQ]

options:
  -h, --help            Show help message
  -f, --file            Specific episode file to replay (from action_logs/)
  -l, --list            List all available logged episodes
  --freq                Publishing frequency for hardware (default: 50.0 Hz)
```

**Examples:**
```bash
# List all episodes
python3 replay_logged_episode.py -l

# Replay specific file at 50Hz
python3 replay_logged_episode.py -f action_logs/time_aware_PID_ckpt1600_steps5000.pkl

# Interactive selection (hardware at 50Hz)
python3 replay_logged_episode.py

# Replay on robot at 100Hz
python3 replay_logged_episode.py -f action_logs/time_aware_PID_ckpt1600_steps5000.pkl --freq 100
```

## Hardware Replay Details

When using `--hardware` flag:
- Actions are published to the ROS2 topic `legs_command` as `Int16MultiArray` messages
- Actions are converted from radians to degrees
- Values are clamped to the int16 range [-120, 120] (motor limits)
- Publishing frequency is maintained with real-time synchronization
- Script waits 2 seconds before starting to allow system to be ready
- Progress is printed every 50 steps with timing information

**ROS2 Topic:**
- Topic: `/legs_command`
- Message Type: `std_msgs/Int16MultiArray`
- Frequency: Configurable (default 50Hz)

**Requirements:**
- ROS2 must be initialized and running
- Robot node must be listening on `/legs_command` topic

## Configuration

### Log Directory

By default, episodes are saved to `action_logs/`. To change this, modify `action_logger.py`:

```python
logger = ActionLogger(log_dir="custom_logs")
```

### Max Steps

Limit episode length using `--max_steps`:

```bash
python3 nubiv6_eval.py -e trapezoidel_200ms --ckpt 500 --log_actions --max_steps 1000
```

## Advanced Features

### Custom Metadata

```python
logger.start_episode(metadata={
    "exp_name": "my_exp",
    "ckpt": 800,
    "environment": "NUBI V6",
    "notes": "Testing new reward function",
    "custom_param": 42
})
```

### Conditional Logging

```python
# Only log every 10th step to reduce file size
step_count = 0
if step_count % 10 == 0:
    logger.log_step(obs, actions)
step_count += 1
```

### Extract Specific Steps from Replay

```python
from action_logger import ActionReplayer

replayer = ActionReplayer("action_logs/episode.pkl")

# Get specific step
step_500 = replayer.get_step(step_idx=500)
action_at_500 = step_500["action"]
print(f"Action at step 500: {action_at_500}")

# Get range of steps
replayer.reset()
first_100_steps = [replayer.get_step() for _ in range(100)]

# Analyze actions
all_actions = replayer.episode_data["actions"]
print(f"Min per joint: {np.min(all_actions, axis=0)}")
print(f"Max per joint: {np.max(all_actions, axis=0)}")
print(f"Mean per joint: {np.mean(all_actions, axis=0)}")
```

### Save Specific Episode Data

```python
from action_logger import ActionReplayer
import numpy as np

replayer = ActionReplayer("action_logs/episode.pkl")

# Extract only actions
actions = replayer.episode_data["actions"]
np.save("episode_actions.npy", actions)

# Export as CSV
import pandas as pd
df = pd.DataFrame(actions)
df.to_csv("episode_actions.csv", index=False)
```

## Troubleshooting

### Logging Issues

**Issue: "No episodes found"**
- Make sure you ran a logging script with `--log_actions` flag
- Check that `action_logs/` directory exists and contains `.pkl` files

**Issue: Replay is slow**
- Logged episodes contain full observation tensors which can be large
- Reduce `--max_steps` when logging to limit file size
- Use SSD storage for faster loading

**Issue: Out of memory during logging**
- Reduce number of steps with `--max_steps`
- Log in multiple shorter episodes instead of one long one
- Use the replayer to analyze shorter segments

### Hardware Replay Issues

**Issue: "Please uninstall 'rsl_rl' and install 'rsl-rl-lib==2.2.4'"**
- This is only needed if Genesis simulation is being used elsewhere
- For hardware replay only, this error will not occur

**Issue: Hardware not receiving commands**
- Ensure ROS2 is running: `ros2 node list`
- Verify robot node is listening: `ros2 topic echo /legs_command`
- Check frequency is reasonable (start with 50Hz)
- Ensure network/serial connection to robot is active

**Issue: "ModuleNotFoundError: No module named 'rclpy'"**
- ROS2 Python environment not set up
- Source ROS2 setup: `source /opt/ros/<distro>/setup.bash`
- Or install rclpy: `pip install rclpy`

**Issue: Commands are clamped or clipped**
- Actions are automatically scaled from radians to degrees and clamped to [-120, 120]
- This is expected behavior for joint position commands
- Ensure your policy outputs are in the correct range

## Performance Notes

- Logging adds minimal overhead (converts tensors to numpy arrays each step)
- Hardware replay maintains real-time synchronization
- File size ≈ (obs_dim + action_dim) × num_steps × 4 bytes (for float32)
- Example: 60 obs features + 12 actions × 10,000 steps ≈ 2.9 MB

**Hardware Replay Timing:**
- 50Hz = 20ms per step
- 100Hz = 10ms per step
- Higher frequencies require faster execution time
- Monitor timing info printed at each step
