# Sim-to-Real Bridge Script

A comprehensive script for testing sine wave commands on both physical and simulated NUBI robot, enabling gap bridging between simulation and reality.

## Features

✅ **Sine Wave Command Generation**: Configurable frequency and amplitude sampled at 50Hz  
✅ **Physical Robot Testing**: Sends commands via ROS `/legs_command` topic, records feedback  
✅ **Simulation Testing**: Runs identical commands in Genesis simulation  
✅ **Comparison Visualization**: Plots command vs physical vs simulated responses  
✅ **Data Persistence**: Saves all test data for later analysis  
✅ **Replay Mode**: Re-run simulation without re-testing physical robot  

## Usage

### Basic Usage (Full Test with Physical Robot)

```bash
python sim_to_real_bridge.py
```

This will:
1. Generate a sine wave command based on your configuration
2. Test on the physical robot (requires ROS and robot to be running)
3. Record feedback from the physical robot
4. Run the exact same commands in simulation
5. Generate comparison plots
6. Save all data to `sim_to_real_data/` directory

### Replay Mode (Simulation Only)

```bash
python sim_to_real_bridge.py replay
```

This will:
1. List all previously saved test data files
2. Prompt you to select one
3. Re-run the simulation with those commands
4. Generate updated plots
5. Create new comparison graphs

## Configuration

Edit the `CONFIG` dictionary at the top of the script to customize:

```python
CONFIG = {
    # Target joint for testing
    "target_joint_idx": 10,           # Index in joint_names list
    "target_joint_name": "LAnkle_pitch",  # Descriptive name
    
    # Sine wave parameters
    "sine_frequency_hz": 1.0,         # Frequency in Hz
    "sine_amplitude_deg": 45.0,       # Amplitude in degrees
    "test_duration_s": 3.0,           # Duration in seconds
    "control_frequency_hz": 50.0,     # Command sampling frequency (50Hz = real robot)
    
    # ROS
    "use_ros": True,                  # Set to False to skip physical robot
    
    # Simulation
    "sim_show_viewer": False,         # Show Genesis viewer
    "sim_gravity": (0.0, 0.0, 0.0),   # Gravity vector
    
    # Data directory
    "data_dir": "sim_to_real_data",
}
```

### Available Joints

```
Index  Joint Name          Comment
-----  ----------          -------
0      RHip_yaw            Right leg
1      RHip_roll
2      RHip_pitch
3      RKnee_pitch
4      RAnkle_roll
5      RAnkle_pitch
6      LHip_yaw            Left leg
7      LHip_roll
8      LHip_pitch
9      LKnee_pitch
10     LAnkle_roll         ← Default for testing
11     LAnkle_pitch        ← Good for ankle tests
```

## Workflow Example

### Test 1: LAnkle_pitch at 1Hz, 45°

```python
CONFIG = {
    "target_joint_idx": 11,
    "target_joint_name": "LAnkle_pitch",
    "sine_frequency_hz": 1.0,
    "sine_amplitude_deg": 45.0,
    "test_duration_s": 3.0,
    ...
}
```

```bash
python sim_to_real_bridge.py
```

**Output:**
- Physical robot commands sent via ROS
- Feedback recorded from `/legs_feedback`
- Simulation runs with same commands
- Comparison plot saved: `comparison_20260522_143015.png`
- Data saved: `bridge_data_20260522_143015.pkl`

### Test 2: Replay Simulation Only

```bash
python sim_to_real_bridge.py replay
```

Select the previous test data to run simulation again without physical robot.

## Output Files

All outputs are saved in `sim_to_real_data/` directory:

```
sim_to_real_data/
├── bridge_data_YYYYMMDD_HHMMSS.pkl    # Pickled data (all test results)
├── comparison_YYYYMMDD_HHMMSS.png     # Comparison plot
└── ...
```

### Data File Contents (pickle format)

```python
{
    "config": {...},                    # Configuration used
    "time_array": array([...]),         # Time points (seconds)
    "commands": array([...]),           # Commanded joint positions (radians)
    "sim_responses": {
        "times": array([...]),
        "positions": array([...]),      # Simulated joint positions
        "velocities": array([...]),     # Simulated joint velocities
        "commanded_values": array([...])
    },
    "physical_responses": {
        "commanded_values": array([...]),
        "command_times": array([...]),
        "feedback_positions": [...],    # Or None if no feedback
        "feedback_velocities": [...],
        "feedback_timestamps": [...]
    }
}
```

## Interpretation of Plots

The generated comparison plots show:

### Position Response (Top)
- **Blue line**: Commanded position (the ideal sine wave)
- **Red line**: Simulated joint position
- **Green line**: Physical robot joint position (if available)

*Ideal behavior:* Red and green lines should closely track the blue line with minimal lag or overshoot.

### Velocity Response (Bottom)
- **Blue line**: Command velocity (derivative of sine wave)
- **Red line**: Simulated joint velocity
- **Green line**: Physical robot joint velocity (if available)

*Ideal behavior:* Simulated and physical velocities should track the command velocity profile.

## Troubleshooting

### ROS Not Available
If ROS is not installed or available:
```python
CONFIG["use_ros"] = False
```
This will skip physical robot testing and only run simulation.

### Physical Robot Not Responding
Check that:
1. ROS is running: `ros2 daemon status`
2. Robot node is active: `ros2 node list`
3. `/legs_command` topic exists: `ros2 topic list`
4. Your script has proper permissions

### Simulation Crashes
Try:
1. Reduce control frequency or duration
2. Decrease sine amplitude
3. Enable `sim_show_viewer = True` to debug visually

### Data Not Saving
Ensure the script has write permissions in the working directory. Create `sim_to_real_data/` manually if needed.

## Advanced Usage

### Modify Control Parameters During Development

```python
# Sweep different frequencies
for freq in [0.5, 1.0, 1.5, 2.0]:
    CONFIG["sine_frequency_hz"] = freq
    main()
```

### Programmatic Data Access

```python
import pickle

# Load previous test
with open("sim_to_real_data/bridge_data_20260522_143015.pkl", 'rb') as f:
    data = pickle.load(f)

# Access components
commands = data["commands"]
sim_pos = data["sim_responses"]["positions"]
phys_pos = data["physical_responses"]["feedback_positions"]
```

## Performance Metrics

After running tests, analyze the gap:

```python
import numpy as np

# Calculate position tracking error
sim_error = np.mean(np.abs(commands - sim_responses["positions"]))
print(f"Simulation error: {sim_error:.4f} rad ({np.rad2deg(sim_error):.2f}°)")
```

## Notes

- **Control Frequency**: Fixed at 50Hz to match real robot hardware
- **Action Scale**: Automatically handled (division by `action_scale=0.25`)
- **Joint Limits**: Commands are clipped to [-120, 120] int16 range for safety
- **Gravity**: Default is zero for cleaner response isolation; adjust for realistic testing
- **Viewer**: Disable viewer (`sim_show_viewer=False`) for faster testing

## Future Enhancements

Potential improvements:
- [ ] Multi-joint testing (sweep multiple joints simultaneously)
- [ ] Frequency response (Bode plots)
- [ ] Phase lag analysis
- [ ] Live plotting during test execution
- [ ] Statistical error metrics
- [ ] PID tuning recommendations based on gap analysis
