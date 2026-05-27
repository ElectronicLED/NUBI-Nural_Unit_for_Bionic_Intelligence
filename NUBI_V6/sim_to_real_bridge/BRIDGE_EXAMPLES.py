"""
Quick-start examples for the sim_to_real_bridge script.

Copy and paste these configurations into the CONFIG section of sim_to_real_bridge.py
to test different scenarios.
"""

# ============================================================================
# EXAMPLE 1: LAnkle Pitch - 1Hz Sine Wave (Default)
# ============================================================================
# Good for: Initial sim-to-real comparison, ankle joint testing
# Joint: LAnkle_pitch (controls ankle flexion/extension of left leg)
# Testing characteristics: Medium speed, gentle oscillation

CONFIG_EXAMPLE_1 = {
    "target_joint_idx": 11,
    "target_joint_name": "LAnkle_pitch",
    "sine_frequency_hz": 1.0,
    "sine_amplitude_deg": 45.0,
    "test_duration_s": 3.0,
    "control_frequency_hz": 50.0,
    "use_ros": True,
    "sim_show_viewer": False,
    "sim_gravity": (0.0, 0.0, 0.0),
    "data_dir": "sim_to_real_data",
}

# ============================================================================
# EXAMPLE 2: RHip Roll - Slow Oscillation (Testing leg spread)
# ============================================================================
# Good for: Testing hip abduction/adduction, stability analysis
# Joint: RHip_roll (controls right leg spread)
# Testing characteristics: Very slow (0.5Hz), good for muscle response time

CONFIG_EXAMPLE_2 = {
    "target_joint_idx": 1,
    "target_joint_name": "RHip_roll",
    "sine_frequency_hz": 0.5,
    "sine_amplitude_deg": 30.0,
    "test_duration_s": 5.0,
    "control_frequency_hz": 50.0,
    "use_ros": True,
    "sim_show_viewer": False,
    "sim_gravity": (0.0, 0.0, 0.0),
    "data_dir": "sim_to_real_data",
}

# ============================================================================
# EXAMPLE 3: RKnee Pitch - Fast Oscillation (Testing joint speed)
# ============================================================================
# Good for: Testing joint responsiveness, high-frequency response
# Joint: RKnee_pitch (controls right knee bending)
# Testing characteristics: Fast (2Hz), tests servo bandwidth

CONFIG_EXAMPLE_3 = {
    "target_joint_idx": 3,
    "target_joint_name": "RKnee_pitch",
    "sine_frequency_hz": 2.0,
    "sine_amplitude_deg": 35.0,
    "test_duration_s": 3.0,
    "control_frequency_hz": 50.0,
    "use_ros": True,
    "sim_show_viewer": False,
    "sim_gravity": (0.0, 0.0, 0.0),
    "data_dir": "sim_to_real_data",
}

# ============================================================================
# EXAMPLE 4: LAnkle Roll - Full Range Test
# ============================================================================
# Good for: Testing full range of motion, maximum amplitude
# Joint: LAnkle_roll (controls ankle inversion/eversion)
# Testing characteristics: Large amplitude, reveals saturation/limits

CONFIG_EXAMPLE_4 = {
    "target_joint_idx": 10,
    "target_joint_name": "LAnkle_roll",
    "sine_frequency_hz": 0.8,
    "sine_amplitude_deg": 60.0,  # Large amplitude!
    "test_duration_s": 4.0,
    "control_frequency_hz": 50.0,
    "use_ros": True,
    "sim_show_viewer": False,
    "sim_gravity": (0.0, 0.0, 0.0),
    "data_dir": "sim_to_real_data",
}

# ============================================================================
# EXAMPLE 5: Simulation Only - No Physical Robot
# ============================================================================
# Good for: Developing/testing script without robot, debugging
# Development scenario: Build confidence in simulation behavior
# Can also use CONFIG["use_ros"] = False in main config

CONFIG_EXAMPLE_5 = {
    "target_joint_idx": 11,
    "target_joint_name": "LAnkle_pitch",
    "sine_frequency_hz": 1.0,
    "sine_amplitude_deg": 45.0,
    "test_duration_s": 3.0,
    "control_frequency_hz": 50.0,
    "use_ros": False,  # Skip ROS/physical robot
    "sim_show_viewer": True,  # Show viewer for debugging
    "sim_gravity": (0.0, 0.0, 0.0),
    "data_dir": "sim_to_real_data",
}

# ============================================================================
# EXAMPLE 6: With Gravity - Realistic Simulation
# ============================================================================
# Good for: Testing with realistic physics, understanding gravity effects
# Scenario: Includes gravity (9.81 m/s^2) for more realistic simulation
# Note: Physical robot will still float, but simulation matches reality

CONFIG_EXAMPLE_6 = {
    "target_joint_idx": 11,
    "target_joint_name": "LAnkle_pitch",
    "sine_frequency_hz": 1.0,
    "sine_amplitude_deg": 45.0,
    "test_duration_s": 3.0,
    "control_frequency_hz": 50.0,
    "use_ros": True,
    "sim_show_viewer": False,
    "sim_gravity": (0.0, 0.0, -9.81),  # Real gravity!
    "data_dir": "sim_to_real_data_with_gravity",
}

# ============================================================================
# EXAMPLE 7: Extended Duration Test
# ============================================================================
# Good for: Thermal testing, servo stability over time, logging behavior
# Scenario: Longer test to see if servo performance degrades

CONFIG_EXAMPLE_7 = {
    "target_joint_idx": 11,
    "target_joint_name": "LAnkle_pitch",
    "sine_frequency_hz": 0.5,  # Slow for duration test
    "sine_amplitude_deg": 30.0,  # Moderate amplitude
    "test_duration_s": 15.0,  # 15 second test
    "control_frequency_hz": 50.0,
    "use_ros": True,
    "sim_show_viewer": False,
    "sim_gravity": (0.0, 0.0, 0.0),
    "data_dir": "sim_to_real_data",
}

# ============================================================================
# HOW TO USE THESE EXAMPLES
# ============================================================================
"""
Step 1: Open sim_to_real_bridge.py
Step 2: Replace the CONFIG dictionary with any example above
Step 3: Run the script:
        
        python sim_to_real_bridge.py

Step 4: For replay mode, use:
        
        python sim_to_real_bridge.py replay

EXAMPLE WORKFLOW:

# Test 1: Quick verification with default settings
# Run Example 1 (LAnkle_pitch - 1Hz) - Use for initial setup

# Test 2: Check servo responsiveness across speeds
# Run Example 2 (0.5Hz slow)
# Run Example 3 (2Hz fast)
# Compare the response plots

# Test 3: Test different joint types
# Run on hip joints (abduction/adduction)
# Run on knee joints (flexion/extension)
# Run on ankle joints (pitch/roll)
# Look for patterns in lag, overshoot, and oscillation

# Test 4: Long-duration thermal testing
# Run Example 7 to check if servo overheats or degrades
# Monitor feedback quality over 15 seconds

# Test 5: Gravity effects
# Run Example 6 with gravity
# Compare position/velocity plots with gravity vs without
# Analyze how gravity affects joint control authority
"""

# ============================================================================
# CUSTOM CONFIGURATION TEMPLATE
# ============================================================================
"""
Copy this template to create your own custom test:

CONFIG_CUSTOM = {
    "target_joint_idx": 11,              # Change this to joint index
    "target_joint_name": "LAnkle_pitch", # Change this to joint name
    "sine_frequency_hz": 1.0,            # Frequency in Hz
    "sine_amplitude_deg": 45.0,          # Amplitude in degrees
    "test_duration_s": 3.0,              # Duration in seconds
    "control_frequency_hz": 50.0,        # Always 50Hz for robot compat
    "use_ros": True,                     # True for physical, False for sim only
    "sim_show_viewer": False,            # True to see Genesis viewer
    "sim_gravity": (0.0, 0.0, 0.0),      # Gravity vector
    "data_dir": "sim_to_real_data",      # Output directory
}

JOINT REFERENCE:
Index  Name              Description
-----  ----              -----------
0      RHip_yaw          Right hip rotation (turn leg left/right)
1      RHip_roll         Right hip abduction (spread leg out)
2      RHip_pitch        Right hip flexion (swing leg forward/back)
3      RKnee_pitch       Right knee flexion (bend knee)
4      RAnkle_roll       Right ankle inversion/eversion (tilt foot)
5      RAnkle_pitch      Right ankle flexion/extension (toe up/down)
6      LHip_yaw          Left hip rotation
7      LHip_roll         Left hip abduction
8      LHip_pitch        Left hip flexion
9      LKnee_pitch       Left knee flexion
10     LAnkle_roll       Left ankle inversion/eversion
11     LAnkle_pitch      Left ankle flexion/extension

TESTING STRATEGY:

1. Start with low frequency (0.5-1 Hz) and moderate amplitude (30-45°)
   → Establishes baseline servo response
   → Identifies major lag or overshoot issues

2. Increase frequency (1-2 Hz) with same amplitude
   → Tests servo bandwidth
   → Reveals phase lag and filtering

3. Test different joints one by one
   → Each joint may have different characteristics
   → Build understanding of robot dynamics

4. Increase amplitude gradually
   → Reveals nonlinearities and saturation
   → Tests joint limits and control saturation

5. Run with gravity for realism
   → Accounts for payload effects
   → More realistic for actual deployment

INTERPRETATION:

GOOD Response (you want this):
- Red and green lines track blue line closely
- Minimal phase lag (<1/4 period)
- Smooth, no oscillation
- Peak velocity reached smoothly

BAD Response (investigate further):
- Large lag between command and response
- Oscillation after movement (underdamped)
- Sluggish response (overdamped)
- Saturation at limits
- Inconsistent physical vs simulated response
"""
