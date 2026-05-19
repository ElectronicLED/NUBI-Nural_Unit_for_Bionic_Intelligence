# NUBI-Nural_Unit_for_Bionic_Intelligence
Born from the ancient ground, built for the future

## Overview
The **NUBI** project aims to develop a robust, adaptive, and generalizable control system for robotic agents using **Reinforcement Learning (RL)**.

This repository contains the primary codebase for developing, training, and testing neural networks that serve as the intelligence unit for the system. We focus on training agents to perform complex motor tasks, learn from errors, and adapt to varying environmental conditions using the Genesis physics simulator and PPO (Proximal Policy Optimization) algorithms.

## Key Goal
To move beyond simple scripted movements and create a truly intelligent bionic unit capable of complex, goal-oriented behavior using state-of-the-art RL algorithms.

## Technology Stack
- **Simulator**: Genesis (physics engine)
- **RL Algorithm**: PPO (via rsl-rl-lib 2.2.4)
- **Hardware Integration**: ROS2
- **Languages**: Python
- **Key Libraries**: PyTorch, NumPy

---

## Project Structure

### Root Level Files
These are template/reference implementations for the Go2 robot:

- **`go2_env.py`** - Environment definition for the Go2 quadruped robot (reference implementation)
- **`go2_eval.py`** - Evaluation/inference script for Go2 policy
- **`go2_train.py`** - Training script for Go2 policy

### Robot Variants

#### **Euflex/** - Early Robot Prototype
First generation robot design with exploration scripts and logs.
- `euflex_env.py` - Environment setup
- `euflex_train.py` - Training script
- `euflex_eval.py` - Evaluation script
- `euflex_resume_training.py` - Resume interrupted training
- `logs/` - Training runs with various configurations (multi-direction, collision avoidance, etc.)
- `meshes/` - Robot mesh files for visualization

#### **Euflex_2/** - Second Generation Euflex
Improved Euflex variant with updated physics and control.
- `Euflex_2.urdf` - Robot URDF definition
- `euflex2_env.py`, `euflex2_train.py`, `euflex2_eval.py` - Training and evaluation
- `logs/` - Training experiments

#### **NUBI_V4/** - NUBI Version 4
Earlier humanoid NUBI design with 20 DOF (degrees of freedom).
- `NUBI_V4.urdf` - Robot URDF definition
- `nubiv4_env.py` - Environment setup
- `nubiv4_train.py` - Training script
- `nubiv4_eval.py` - Evaluation script
- `nubiv4_resume_training.py` - Resume training
- `debug_collisions.py` - Debug collision issues
- `hardwareLink.py` - Hardware communication layer
- `logs/` - Various training experiments (time-aware control, substepping variants, etc.)
- `meshes/` - Robot mesh files

#### **NUBI_V6/** - Current Main Version ⭐
Latest humanoid NUBI design (production version).
- `NUBI_V6.urdf` - Robot URDF definition with 20 DOF
- `nubiv6_env.py` - **Environment definition** - Core simulation environment
- `nubiv6_train.py` - **Main training script** - Trains policies using PPO
- `nubiv6_eval.py` - **Evaluation/inference** - Tests trained policies with visualization
- `nubiv6_resume_training.py` - **Resume training** - Continues from checkpoint
- `nubiv6_playground.py` - **Interactive testing** - Manual control and exploration with keyboard input
- `replay_logged_episode.py` - **Hardware replay** - Replays logged episodes on physical robot via ROS2
- `action_logger.py` - **Action logging utility** - Records actions, observations, and episode data
- `debug_collisions.py` - **Collision debugging** - Debug and diagnose collision issues
- `hardwareLink.py` - **Hardware interface** - ROS2 communication layer with physical robot
- `logs/` - Trained models and experiment logs (20+ variants)
  - Each subdirectory contains: `model_X.pt` (checkpoints), `events.out.tfevents.*` (training metrics)
  - Notable experiments: `JR1/2/3_P254_D15/`, `kind_policy/`, `substepping_*`, `trapezoidal_*`
- `action_logs/` - Directory for storing logged episodes (created during evaluation with `--log_actions`)
- `meshes/` - Robot mesh files for visualization
- `ACTION_LOGGING_README.md` - Documentation for action logging system

#### **toby/** - Alternative Robot Design
Different robot configuration for experimentation.
- `toby.urdf` - Robot URDF
- `meshes/` - Mesh files

---

## File Interactions & Workflow

### Training Pipeline for NUBI_V6

```
nubiv6_train.py
    ├─→ imports nubiv6_env.py (creates simulation environment)
    ├─→ imports rsl_rl (PPO algorithm)
    └─→ generates:
        ├─ logs/{exp_name}/model_X.pt (checkpoints)
        ├─ logs/{exp_name}/cfgs.pkl (configuration snapshots)
        └─ logs/{exp_name}/events.out.tfevents.* (TensorBoard metrics)

nubiv6_resume_training.py
    ├─→ loads saved cfgs.pkl from logs/{exp_name}/
    ├─→ loads model checkpoint (model_X.pt)
    └─→ continues training from checkpoint
```

### Evaluation Pipeline for NUBI_V6

```
nubiv6_eval.py
    ├─→ imports nubiv6_env.py (creates single environment with viewer)
    ├─→ loads trained policy from logs/{exp_name}/model_X.pt
    ├─→ runs inference in Genesis viewer (interactive visualization)
    ├─→ optionally imports action_logger.py (if --log_actions flag)
    │   └─→ records observations and actions to action_logs/
    └─→ displays policy behavior in real-time
```

### Hardware Deployment Pipeline

```
nubiv6_playground.py (manual control)
    └─→ hardwareLink.py → ROS2 publisher (sends commands to robot)

replay_logged_episode.py (automated replay)
    ├─→ loads pickled episode data from action_logs/
    ├─→ imports ActionReplayer from action_logger.py
    ├─→ hardwareLink.py → ROS2 publisher
    └─→ replays actions on physical robot at 50Hz
```

### Debug & Utility

```
debug_collisions.py
    ├─→ imports nubiv6_env.py
    ├─→ identifies collision pairs
    └─→ helps diagnose self-collision issues

action_logger.py
    ├─→ ActionLogger class: records simulation data
    ├─→ ActionReplayer class: replays episodes on hardware
    └─→ used by: nubiv6_eval.py, replay_logged_episode.py
```

---

## How to Run Each File

### Prerequisites
```bash
# Install required packages
pip install genesis rsl-rl-lib==2.2.4 torch numpy

# For hardware deployment only
pip install rclpy std_msgs pyopengl playsound
```

### NUBI_V6 Main Scripts (Recommended Starting Point)

#### 1. **Training a New Policy**
```bash
cd NUBI_V6
python nubiv6_train.py -e {exp_name} -B {num_envs} --max_iterations {iterations}
```
**Parameters:**
- `-e, --exp_name`: Experiment name (default: "time_aware_replicate")
- `-B, --num_envs`: Number of parallel environments for training (default: 4096)
- `--max_iterations`: Maximum training iterations (default: 500)

**Output:**
- Saves to `logs/{exp_name}/model_X.pt` (checkpoints every 100 iterations)
- Saves `logs/{exp_name}/cfgs.pkl` (configuration)
- Saves TensorBoard logs for monitoring

**Example:**
```bash
python nubiv6_train.py -e my_first_policy -B 2048 --max_iterations 1000
```

#### 2. **Evaluate a Trained Policy**
```bash
cd NUBI_V6
python nubiv6_eval.py -e {exp_name} --ckpt {checkpoint}
```
**Parameters:**
- `-e, --exp_name`: Experiment name to load from `logs/`
- `--ckpt`: Checkpoint number (e.g., 1600, 1000)
- `--log_actions`: Enable action logging to `action_logs/`
- `--max_steps`: Maximum steps to run (None = infinite)

**Output:**
- Opens Genesis viewer with interactive visualization
- If `--log_actions`: Saves episode data to `action_logs/{exp_name}_ckpt{checkpoint}_steps{steps}.pkl`

**Examples:**
```bash
# Just view the policy
python nubiv6_eval.py -e kind_policy --ckpt 1000

# Log actions for 5000 steps
python nubiv6_eval.py -e time_aware_PID --ckpt 1600 --log_actions --max_steps 5000
```

#### 3. **Resume Training from Checkpoint**
```bash
cd NUBI_V6
python nubiv6_resume_training.py -e {exp_name} -B {num_envs} --max_iterations {iterations}
```
**Parameters:**
- Same as training script
- Automatically loads the last checkpoint from logs

**Example:**
```bash
python nubiv6_resume_training.py -e my_first_policy -B 2048 --max_iterations 2000
```

#### 4. **Interactive Playground (Manual Control)**
```bash
cd NUBI_V6
python nubiv6_playground.py
```
**Features:**
- Keyboard-controlled robot movement
- Manual testing of hardware commands via ROS2
- Real-time viewer with Genesis
- No trained policy needed

#### 5. **Debug Collisions**
```bash
cd NUBI_V6
python debug_collisions.py
```
**Purpose:**
- Identifies collision pairs in the robot
- Helps diagnose self-collision issues
- Useful for tuning simulator parameters

#### 6. **Replay Logged Episode on Hardware**
```bash
cd NUBI_V6
python replay_logged_episode.py -l  # List available episodes
python replay_logged_episode.py {episode_file} --target_freq 50.0 --publish_angles True
```
**Parameters:**
- `-l`: List available logged episodes
- Episode file: Path or filename from `action_logs/`
- `--target_freq`: Publishing frequency in Hz (default: 50Hz)
- `--publish_angles`: Replay recorded joint angles or compute from actions
- `--action_scale`: Scale factor for actions

**Example:**
```bash
python replay_logged_episode.py action_logs/time_aware_PID_ckpt1600_steps5000.pkl --target_freq 50.0
```

---

### Root Level Scripts (Reference/Alternative Robots)

#### Go2 Robot Training
```bash
python go2_train.py -e go2_experiment -B 4096 --max_iterations 500
python go2_eval.py -e go2_experiment --ckpt 500
```

#### Euflex Robot Training
```bash
cd Euflex
python euflex_train.py -e euflex_experiment -B 4096
python euflex_eval.py -e euflex_experiment --ckpt 500
```

#### NUBI V4 Training
```bash
cd NUBI_V4
python nubiv4_train.py -e nubiv4_experiment -B 4096
python nubiv4_eval.py -e nubiv4_experiment --ckpt 500
```

---

## Training Configuration

Training hyperparameters are defined in each `*_train.py` file in the `get_train_cfg()` function:

**Key PPO Hyperparameters:**
- `learning_rate`: 0.001
- `clip_param`: 0.2 (PPO clipping parameter)
- `num_learning_epochs`: 5
- `num_mini_batches`: 4
- `gamma`: 0.99 (discount factor)
- `lam`: 0.95 (GAE lambda)
- `entropy_coef`: 0.01

**Network Architecture:**
- Actor hidden dims: [512, 256, 128]
- Critic hidden dims: [512, 256, 128]
- Activation: ELU

**Simulation Parameters:**
- Physics DT: 0.004s (1000 Hz)
- Control DT: 0.02s (50 Hz, matches real robot)
- Control substeps: 20 per RL action

---

## Understanding the Logs Directory

Each training run creates a directory in `logs/{exp_name}/`:

```
logs/kind_policy/
├── model_0.pt                                    # Initial random policy
├── model_100.pt                                  # Checkpoint at iteration 100
├── model_1000.pt                                 # Final policy
├── cfgs.pkl                                      # Pickled configurations (env, obs, reward, command, train)
└── events.out.tfevents.1776541209...            # TensorBoard event file for metrics
```

**View Training Metrics:**
```bash
tensorboard --logdir=NUBI_V6/logs/
```

Then open `http://localhost:6006` in your browser.

---

## Expected Problems & Solutions

#### 1. OpenGL.error.Error: Attempt to retrieve context when no valid context
**Solution:**
https://github.com/Genesis-Embodied-AI/Genesis/issues/609

Set these environment variables before running scripts:
```bash
export MUJOCO_GL=glx
export PYOPENGL_PLATFORM=glx
```

Or add to your `.bashrc`:
```bash
echo 'export MUJOCO_GL=glx' >> ~/.bashrc
echo 'export PYOPENGL_PLATFORM=glx' >> ~/.bashrc
source ~/.bashrc
```

#### 2. Robot Collides with Itself
**Temporary Solution:**
Go to `~/.local/lib/python3.10/site-packages/genesis/options`
In file `solvers.py`, find the class `RigidOptions`
Set default: `enable_self_collision: bool = True`

This is a temporary solution until per-instance option configuration is implemented.

#### 3. ImportError for rsl_rl
**Solution:**
Ensure you have the correct version installed:
```bash
pip uninstall rsl_rl rsl-rl-lib -y
pip install rsl-rl-lib==2.2.4
```

#### 4. ROS2 Connection Issues
**Solution:**
Ensure ROS2 is installed and sourced:
```bash
source /opt/ros/{ros_version}/setup.bash
```

And the NUBI_V6 firmware is running on the robot hardware. Check robot control branch