"""
Simulation to Real Bridge Script

This script generates a sine wave command, tests it on the physical robot,
records the response, and compares it with simulation.

Features:
- Generates sine wave at defined frequency and amplitude
- Sends commands to physical robot at 50Hz via ROS /legs_command topic
- Records feedback from /legs_feedback topic
- Runs the exact same commands in simulation
- Plots comparison graphs (command vs physical vs simulated response)
- Allows replaying simulation without re-testing physical robot
- Saves data for later analysis
"""

import numpy as np
import torch
import matplotlib.pyplot as plt
import time
import os
import sys
from datetime import datetime
from pathlib import Path
import pickle
import genesis as gs
from threading import Thread

# Import from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from nubiv6_env import NubiEnv
from nubiv6_train import get_cfgs

# ===========================
# CONFIGURATION SECTION
# ===========================
CONFIG = {
    # Sine wave parameters
    "target_joint_idx": 10,  # LAnkle_roll (index 10 in joint_names list)
    "target_joint_name": "LAnkle_roll",  # Easy to identify which joint
    "sine_frequency_hz": 0.5,  # Hz
    "sine_amplitude_deg": 45.0,  # degrees (will be converted to radians)
    "test_duration_s": 5.0,  # seconds
    "control_frequency_hz": 50.0,  # ROS command frequency
    "zero_padding_duration_s": 10.0,  # Duration of zeros before sine wave starts (seconds)
    
    # ROS parameters
    "use_ros": True,  # Set to False to skip ROS testing
    "play_time_ms": 35,  # Command play time in milliseconds (20ms for 50Hz)
    "ros_timeout_s": 10.0,
    
    # Simulation parameters
    "sim_show_viewer": True,
    "sim_gravity": (0.0, 0.0, 0.0),  # No gravity for isolating joint response
    
    # Data save directory
    "data_dir": "sim_to_real_data",
}

# ===========================
# HELPER FUNCTIONS
# ===========================

def setup_data_directory():
    """Create data directory if it doesn't exist."""
    os.makedirs(CONFIG["data_dir"], exist_ok=True)
    return CONFIG["data_dir"]

def generate_sine_commands(duration, frequency, amplitude_rad, control_freq, zero_padding_s=0.0):
    """
    Generate sine wave commands with optional zero padding at the start.
    
    Args:
        duration: Duration in seconds
        frequency: Frequency in Hz
        amplitude_rad: Amplitude in radians
        control_freq: Control frequency in Hz
        zero_padding_s: Duration of zero padding before sine wave starts (seconds)
    
    Returns:
        time_array: Time points
        commands: Command values (in radians)
    """
    dt = 1.0 / control_freq
    num_samples = int(duration / dt) + 1
    time_array = np.arange(num_samples) * dt
    commands = amplitude_rad * np.sin(2 * np.pi * frequency * time_array)
    
    # Add zero padding at the beginning
    if zero_padding_s > 0:
        num_zero_samples = int(zero_padding_s / dt)
        zero_padding = np.zeros(num_zero_samples)
        commands = np.concatenate([zero_padding, commands])
        # Adjust time array to account for added samples
        time_array = np.arange(len(commands)) * dt
    
    return time_array, commands

def initialize_ros():
    """Initialize ROS node and create publishers/subscribers."""
    try:
        import rclpy
        from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
        from std_msgs.msg import Int16MultiArray
        from sensor_msgs.msg import JointState
            
        if not rclpy.ok():
            rclpy.init()
        
        node = rclpy.create_node("sim_to_real_bridge")
        
        # Debug: List available topics
        print("[ROS] Discovering available topics...")
        topic_names_and_types = node.get_topic_names_and_types()
        feedback_topics = [name for name, types in topic_names_and_types if 'feedback' in name.lower()]
        print(f"[ROS] Available feedback topics: {feedback_topics}")
        
        # Show message types for feedback topics
        for topic_name, types in topic_names_and_types:
            if 'feedback' in topic_name.lower():
                print(f"[ROS] {topic_name}: {types}")
        
        # Publisher for leg commands
        publisher = node.create_publisher(Int16MultiArray, "legs_command", 10)
        
        # Subscriber for feedback with more permissive QoS
        feedback_data = {
            "positions": [],  # Will store int16 array values
            "timestamps": [],
            "latest_position": None,
            "callback_count": 0,
            "last_msg": None
        }
        
        def feedback_callback(msg):
            try:
                feedback_data["callback_count"] += 1
                # Update the buffer with the newest data. DO NOT append to lists here.
                if hasattr(msg, 'data'):
                    feedback_data["latest_position"] = list(msg.data)

                feedback_data["last_msg"] = str(msg.data)[:100] if hasattr(msg, 'data') else "no data"

                # Print every Nth callback to avoid spam
                if feedback_data["callback_count"] % 10 == 0:
                    print(f"[CALLBACK] Received message #{feedback_data['callback_count']}")
            except Exception as e:
                print(f"[ERROR] Callback exception: {e}")
        
        # Use BEST_EFFORT QoS to match the robot's publisher
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=100  # Increased depth
        )
        
        try:
            subscriber = node.create_subscription(
                Int16MultiArray,  # Changed from JointState to Int16MultiArray
                "legs_feedback", 
                feedback_callback, 
                qos_profile
            )
            print("[ROS] Successfully subscribed to /legs_feedback with Int16MultiArray type")
        except Exception as e:
            print(f"[WARNING] Could not subscribe with Int16MultiArray: {e}")
            subscriber = None
        
        print("[ROS] Node initialized (synchronous mode)")
        
        return node, publisher, feedback_data
    except Exception as e:
        print(f"[ERROR] ROS initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def send_ros_command(publisher, node, joint_idx, command_value, all_joints_config):
    """
    Send a command to the robot via ROS.
    
    Args:
        publisher: ROS publisher
        node: ROS node for spinning
        joint_idx: Index of the target joint
        command_value: Command value in radians
        all_joints_config: Configuration dict with action_scale
    """
    if publisher is None:
        return
    
    try:
        import rclpy
        from std_msgs.msg import Int16MultiArray
        
        # Create command array for all 12 joints (zeros except target joint)
        command_array = np.zeros(12)
        # Convert from radians to degrees for physical robot
        command_array[joint_idx] = np.rad2deg(command_value)
        
        # Convert directly to int16 (robot's native format) without RL scaling
        scaled_commands = np.clip(command_array, -120, 120).astype(np.int16)
        
        data_list = [int(x) for x in scaled_commands]
        data_list.append(CONFIG["play_time_ms"])

        msg = Int16MultiArray()
        msg.data = data_list
        publisher.publish(msg)
        
        
        rclpy.spin_once(node, timeout_sec=0.00)  # 20ms timeout
        
        
    except Exception as e:
        print(f"Error sending ROS command: {e}")

def test_physical_robot(env_cfg, commands, time_array):
    """
    Test commands on the physical robot via ROS.
    
    Args:
        env_cfg: Environment configuration
        commands: Array of command values (in radians)
        time_array: Time points for each command
    
    Returns:
        physical_responses: Dictionary with recorded joint positions/velocities
    """
    print("\n" + "="*60)
    print("PHYSICAL ROBOT TEST")
    print("="*60)
    
    node, publisher, feedback_data = initialize_ros()
    
    if publisher is None:
        print("Cannot test physical robot: ROS not available")
        return None
    
    joint_idx = CONFIG["target_joint_idx"]
    dt = 1.0 / CONFIG["control_frequency_hz"]
    
    print(f"Testing joint: {CONFIG['target_joint_name']} (index {joint_idx})")
    print(f"Frequency: {CONFIG['sine_frequency_hz']} Hz")
    print(f"Amplitude: {CONFIG['sine_amplitude_deg']} degrees")
    print(f"Duration: {CONFIG['test_duration_s']} seconds")
    print(f"Number of samples: {len(commands)}")
    
    # Pre-spin to make sure subscriber is ready
    print("\nPre-spinning node to initialize subscribers...")
    import rclpy
    for i in range(10):
        rclpy.spin_once(node, timeout_sec=0.05)
        time.sleep(0.01)
    print("Subscriber ready.")
    
    print("\nStarting test in 2 seconds...")
    time.sleep(2)

    # Clear out the stationary data collected during pre-spin and sleep
    feedback_data["positions"].clear()
    feedback_data["timestamps"].clear()
    feedback_data["latest_position"] = None
    feedback_data["callback_count"] = 0
    
    start_time = time.time()
    commanded_values = []
    command_times = []
    
    try:
        for i, (t, cmd) in enumerate(zip(time_array, commands)):
            # Send command
            send_ros_command(publisher, node, joint_idx, cmd, env_cfg)
            commanded_values.append(cmd)
            command_times.append(time.time() - start_time)
            
            if (i + 1) % 50 == 0:  # Print progress every second at 50Hz
                print(f"  Sent {i+1}/{len(commands)} commands ({(i+1)*dt:.2f}s/{CONFIG['test_duration_s']}s)")
            
            # Wait until next control step, processing messages while waiting
            import rclpy
            elapsed = time.time() - start_time - t
            if elapsed < 0:
                remaining = -elapsed
                # Break up the wait time to process messages multiple times
                steps = max(1, int(remaining * 50))  # 50 steps per second
                step_time = remaining / steps
                for _ in range(steps):
                    rclpy.spin_once(node, timeout_sec=0.001)
                    time.sleep(step_time * 0.95)

            # The wait time is over, meaning we are exactly at time `t`.
            # Grab the freshest telemetry data from the callback buffer.
            if feedback_data["latest_position"] is not None:
                feedback_data["positions"].append(feedback_data["latest_position"])
                # Lock the timestamp exactly to the ideal control time
                feedback_data["timestamps"].append(start_time + t)
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Send zero command at the end
        send_ros_command(publisher, node, joint_idx, 0.0, env_cfg)
        time.sleep(0.5)
    
    print(f"\nPhysical test completed.")
    print(f"  Callback invocations: {feedback_data.get('callback_count', 0)}")
    print(f"  Feedback samples recorded: {len(feedback_data['timestamps'])}")
    if feedback_data.get('last_msg'):
        print(f"  Last message preview: {feedback_data['last_msg']}")
    
    physical_responses = {
        "commanded_values": np.array(commanded_values),
        "command_times": np.array(command_times),
        "feedback_positions": feedback_data["positions"],
        "feedback_timestamps": feedback_data["timestamps"],
    }
    
    return physical_responses

def test_simulation(env_cfg, obs_cfg, reward_cfg, command_cfg, commands, time_array, joint_idx):
    """
    Test the same commands in simulation.
    
    Args:
        env_cfg, obs_cfg, reward_cfg, command_cfg: Environment configurations
        commands: Array of command values (in radians)
        time_array: Time points for each command
        joint_idx: Index of target joint
    
    Returns:
        sim_responses: Dictionary with recorded joint positions/velocities
    """
    print("\n" + "="*60)
    print("SIMULATION TEST")
    print("="*60)
    
    # Modify env config for floating robot
    env_cfg["base_init_pos"] = [0.0, 0.0, 0.4]
    env_cfg["gravity"] = CONFIG["sim_gravity"]
    
    # Initialize Genesis
    gs.init()
    
    # Create environment with 1 environment
    env = NubiEnv(
        num_envs=1,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=CONFIG["sim_show_viewer"],
    )
    
    print(f"Testing joint: {CONFIG['target_joint_name']} (index {joint_idx})")
    print(f"Duration: {CONFIG['test_duration_s']} seconds")
    print(f"Simulation steps per RL action: {env.control_substeps}")
    
    # Reset environment
    obs, _ = env.reset()
    
    # Storage for simulation data
    sim_times = []
    sim_positions = []
    sim_velocities = []
    commanded_values = []
    
    # Send commands to simulation
    print("\nRunning simulation...")
    for i, (t, cmd) in enumerate(zip(time_array, commands)):
        # Create action array (zeros except for target joint)
        action = torch.zeros((1, 12), device=gs.device)
        action[0, joint_idx] = cmd / env_cfg["action_scale"]
        
        # Step simulation
        obs, reward, reset, extras = env.step(action)
        
        # Record joint position and velocity
        dof_positions = env.dof_pos[0].cpu().numpy()
        dof_velocities = env.dof_vel[0].cpu().numpy()
        
        sim_times.append(t)
        sim_positions.append(dof_positions[joint_idx])
        sim_velocities.append(dof_velocities[joint_idx])
        commanded_values.append(cmd)
        
        if (i + 1) % 50 == 0:
            print(f"  Simulated {i+1}/{len(commands)} steps")
    
    print(f"Simulation completed. Recorded {len(sim_times)} steps.")
    
    sim_responses = {
        "times": np.array(sim_times),
        "positions": np.array(sim_positions),
        "velocities": np.array(sim_velocities),
        "commanded_values": np.array(commanded_values),
        "kp_scale": env.kp_scale,
        "kd_scale": env.kd_scale,
    }
    
    return sim_responses

def save_data(data, filename):
    """Save data to pickle file."""
    filepath = os.path.join(CONFIG["data_dir"], filename)
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)
    print(f"Data saved to {filepath}")
    return filepath

def load_data(filename):
    """Load data from pickle file."""
    filepath = os.path.join(CONFIG["data_dir"], filename)
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    print(f"Data loaded from {filepath}")
    return data

def plot_comparison(commands, time_array, sim_responses, physical_responses=None, env_cfg=None):
    """
    Create comparison plots of commands vs responses.
    
    Args:
        commands: Original command values
        time_array: Time points
        sim_responses: Simulation response data
        physical_responses: Physical robot response data (optional)
        env_cfg: Environment configuration for action_scale (optional)
    """
    if env_cfg is None:
        env_cfg = {"action_scale": 0.25}  # Default fallback
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Position response
    ax = axes[0]
    ax.plot(time_array, commands, 'b-', linewidth=2, label='Commanded Position', alpha=0.8)
    ax.plot(sim_responses["times"], sim_responses["positions"], 'r-', linewidth=2, label='Simulated Position', alpha=0.8)
    
    if physical_responses is not None:
        try:
            positions_data = physical_responses.get("feedback_positions", [])
            if positions_data and len(positions_data) > 0:
                print(f"[DEBUG] Plotting physical data: {len(positions_data)} samples")
                feedback_times = np.array(physical_responses["feedback_timestamps"]) - physical_responses["feedback_timestamps"][0]
                # Extract position of target joint from the array
                feedback_positions_raw = np.array(positions_data)[:, CONFIG["target_joint_idx"]]
                # feedback_positions_raw is in scaled int16 format, convert back to degrees
                feedback_positions = feedback_positions_raw 
                # Convert from degrees to radians for comparison with simulation
                feedback_positions = np.deg2rad(feedback_positions)
                print(f"[DEBUG] Position range: {np.min(feedback_positions):.4f} to {np.max(feedback_positions):.4f} rad")
                # Assuming the flatline lasts about 1.2 seconds based on your graph
                queue_delay_s = 0.0 
                adjusted_feedback_times = feedback_times - queue_delay_s

                # Plot using the adjusted time
                ax.plot(adjusted_feedback_times, feedback_positions, 'g-', linewidth=2, label='Physical Position')
                #ax.plot(feedback_times, feedback_positions, 'g-', linewidth=2, label='Physical Position', alpha=0.8)
            else:
                print(f"[DEBUG] No physical position data to plot")
        except Exception as e:
            print(f"Warning: Could not plot physical position data: {e}")
            import traceback
            traceback.print_exc()
    
    ax.set_xlabel('Time (s)', fontsize=11)
    ax.set_ylabel('Joint Position (rad)', fontsize=11)
    ax.set_title(f'Position Response: {CONFIG["target_joint_name"]}', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Plot 2: Velocity response
    ax = axes[1]
    # Compute command velocity (derivative of command)
    cmd_vel = np.gradient(commands, time_array)
    ax.plot(time_array, cmd_vel, 'b-', linewidth=2, label='Commanded Velocity', alpha=0.8)
    ax.plot(sim_responses["times"], sim_responses["velocities"], 'r-', linewidth=2, label='Simulated Velocity', alpha=0.8)
    
    # Note: Physical feedback is Int16MultiArray, which doesn't include velocity data
    
    ax.set_xlabel('Time (s)', fontsize=11)
    ax.set_ylabel('Joint Velocity (rad/s)', fontsize=11)
    ax.set_title(f'Velocity Response: {CONFIG["target_joint_name"]}', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    
    # Save figure with kp_scale and kd_scale in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    kp_scale = sim_responses.get("kp_scale", None)
    kd_scale = sim_responses.get("kd_scale", None)
    
    if kp_scale is not None and kd_scale is not None:
        figpath = os.path.join(CONFIG["data_dir"], f"comparison_{timestamp}_kp{kp_scale:.4f}_kd{kd_scale:.5f}.png")
    else:
        figpath = os.path.join(CONFIG["data_dir"], f"comparison_{timestamp}.png")
    
    plt.savefig(figpath, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {figpath}")
    
    plt.show()

# ===========================
# MAIN SCRIPT
# ===========================

def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("SIM-TO-REAL BRIDGE SCRIPT")
    print("="*60)
    
    # Setup
    setup_data_directory()
    
    # Print configuration
    print("\nConfiguration:")
    print(f"  Target Joint: {CONFIG['target_joint_name']} (index {CONFIG['target_joint_idx']})")
    print(f"  Sine Wave: {CONFIG['sine_frequency_hz']} Hz, {CONFIG['sine_amplitude_deg']}° amplitude")
    print(f"  Duration: {CONFIG['test_duration_s']} seconds @ {CONFIG['control_frequency_hz']} Hz")
    print(f"  Use ROS: {CONFIG['use_ros']}")
    
    # Load configurations
    env_cfg, obs_cfg, reward_cfg, command_cfg = get_cfgs()
    
    # Convert amplitude to radians
    amplitude_rad = np.deg2rad(CONFIG["sine_amplitude_deg"])
    
    # Generate commands
    print("\nGenerating sine wave commands...")
    time_array, commands = generate_sine_commands(
        CONFIG["test_duration_s"],
        CONFIG["sine_frequency_hz"],
        amplitude_rad,
        CONFIG["control_frequency_hz"],
        CONFIG["zero_padding_duration_s"]
    )
    print(f"Generated {len(commands)} commands")
    print(f"  Min: {np.min(commands):.4f} rad ({np.rad2deg(np.min(commands)):.2f}°)")
    print(f"  Max: {np.max(commands):.4f} rad ({np.rad2deg(np.max(commands)):.2f}°)")
    
    # Test physical robot
    physical_responses = None
    if CONFIG["use_ros"]:
        try:
            physical_responses = test_physical_robot(env_cfg, commands, time_array)
        except Exception as e:
            print(f"Error during physical robot test: {e}")
            physical_responses = None
    else:
        print("\nSkipping physical robot test (use_ros=False)")
    
    # Test simulation
    try:
        sim_responses = test_simulation(
            env_cfg, obs_cfg, reward_cfg, command_cfg,
            commands, time_array, CONFIG["target_joint_idx"]
        )
    except Exception as e:
        print(f"Error during simulation: {e}")
        raise
    
    # Save data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_to_save = {
        "config": CONFIG,
        "time_array": time_array,
        "commands": commands,
        "sim_responses": sim_responses,
        "physical_responses": physical_responses,
    }
    
    save_data(data_to_save, f"bridge_data_{timestamp}.pkl")
    
    # Plot comparison
    print("\nGenerating comparison plots...")
    plot_comparison(commands, time_array, sim_responses, physical_responses, env_cfg)
    
    print("\n" + "="*60)
    print("SCRIPT COMPLETED SUCCESSFULLY")
    print("="*60)

def replay_simulation_only():
    """Replay a previous test in simulation without retesting physical robot."""
    print("\n" + "="*60)
    print("SIMULATION REPLAY")
    print("="*60)
    
    # List available data files
    data_dir = CONFIG["data_dir"]
    pkl_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.pkl')])
    
    if not pkl_files:
        print("No saved data files found!")
        return
    
    print("\nAvailable data files:")
    for i, fname in enumerate(pkl_files):
        print(f"  {i+1}. {fname}")
    
    choice = int(input("\nSelect file number to replay: ")) - 1
    if 0 <= choice < len(pkl_files):
        data = load_data(pkl_files[choice])
        
        # Extract original config and commands
        CONFIG.update(data["config"])
        commands = data["commands"]
        time_array = data["time_array"]
        
        # Load configs
        env_cfg, obs_cfg, reward_cfg, command_cfg = get_cfgs()
        
        # Run simulation
        sim_responses = test_simulation(
            env_cfg, obs_cfg, reward_cfg, command_cfg,
            commands, time_array, CONFIG["target_joint_idx"]
        )
        
        # Plot
        plot_comparison(commands, time_array, sim_responses, data["physical_responses"], env_cfg)
    else:
        print("Invalid selection")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "replay":
        replay_simulation_only()
    else:
        main()
