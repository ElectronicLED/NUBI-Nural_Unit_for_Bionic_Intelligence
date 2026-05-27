#!/usr/bin/env python3
"""
QUICK REFERENCE - Sim-to-Real Bridge Script

Copy-paste commands and configurations for common tasks.
"""

# ============================================================================
# COMMAND LINE USAGE
# ============================================================================

"""
# Full test (physical robot + simulation)
python sim_to_real_bridge.py

# Simulation replay (choose previous test)
python sim_to_real_bridge.py replay

# For debugging (show Genesis viewer)
# Edit CONFIG["sim_show_viewer"] = True, then:
python sim_to_real_bridge.py
"""

# ============================================================================
# FASTEST SETUP - Minimal Code Changes
# ============================================================================

"""
To test a different joint, only change ONE line in the CONFIG dict:

Current (LAnkle_pitch):
    "target_joint_idx": 11,

Change to test other joints:

Right leg joints:
    "target_joint_idx": 0,   # RHip_yaw
    "target_joint_idx": 1,   # RHip_roll (GOOD for testing)
    "target_joint_idx": 2,   # RHip_pitch
    "target_joint_idx": 3,   # RKnee_pitch (GOOD for testing)
    "target_joint_idx": 4,   # RAnkle_roll
    "target_joint_idx": 5,   # RAnkle_pitch

Left leg joints:
    "target_joint_idx": 6,   # LHip_yaw
    "target_joint_idx": 7,   # LHip_roll (GOOD for testing)
    "target_joint_idx": 8,   # LHip_pitch
    "target_joint_idx": 9,   # LKnee_pitch (GOOD for testing)
    "target_joint_idx": 10,  # LAnkle_roll (GOOD for testing)
    "target_joint_idx": 11,  # LAnkle_pitch (DEFAULT)
"""

# ============================================================================
# COMMON TESTING PATTERNS
# ============================================================================

"""
PATTERN 1: First time setup
═════════════════════════════
1. Keep all defaults in CONFIG
2. Run: python sim_to_real_bridge.py
3. Check console output for any errors
4. Look at generated comparison_*.png plot
5. Compare physical (green) vs simulated (red) vs command (blue)

PATTERN 2: Test servo responsiveness
═════════════════════════════════════
# Test slow motion (0.5 Hz)
"sine_frequency_hz": 0.5,
python sim_to_real_bridge.py

# Then test fast motion (2 Hz)
"sine_frequency_hz": 2.0,
python sim_to_real_bridge.py

# Compare plots - faster frequency should show phase lag

PATTERN 3: Find joint limits
════════════════════════════
# Start with moderate amplitude
"sine_amplitude_deg": 45.0,

# If successful, increase:
"sine_amplitude_deg": 60.0,
python sim_to_real_bridge.py

# Keep increasing until physical robot hits limits
# Or response becomes distorted (saturation)

PATTERN 4: Quick simulation-only check
═══════════════════════════════════════
"use_ros": False,  # Skip physical robot
python sim_to_real_bridge.py

# Fast! Just runs simulation, no ROS overhead

PATTERN 5: Gravity effects analysis
═══════════════════════════════════
# Test 1: Without gravity (current)
"sim_gravity": (0.0, 0.0, 0.0),
python sim_to_real_bridge.py

# Save the plots/data

# Test 2: With realistic gravity
"sim_gravity": (0.0, 0.0, -9.81),
python sim_to_real_bridge.py

# Compare how gravity affects response
"""

# ============================================================================
# INTERPRETING RESULTS
# ============================================================================

"""
POSITION PLOT (Top graph):
═════════════════════════

Blue line = Your commanded sine wave (should be perfect sine)
Red line = Simulated joint response
Green line = Physical robot response (if available)

GOOD SIGNS:
✓ Red and green lines track blue line closely
✓ Lines start moving at the beginning (no delay)
✓ Lines reach peaks at expected times
✓ Smooth motion, no jitters or oscillations
✓ Red and green lines are close to each other

BAD SIGNS:
✗ Large lag between blue and red/green (delayed response)
✗ Red overshoots blue (servo goes too far)
✗ Red oscillates around blue (underdamped)
✗ Red barely moves toward blue (servo too slow)
✗ Red and green lines differ significantly (sim != real mismatch)


VELOCITY PLOT (Bottom graph):
════════════════════════════

Blue line = Command velocity (peak/valley derivatives)
Red line = Simulated velocity
Green line = Physical velocity

GOOD SIGNS:
✓ Red/green velocities peak at same time as blue
✓ Peak magnitudes similar to commanded
✓ Smooth curves, minimal noise
✓ Velocity transitions are smooth

BAD SIGNS:
✗ Velocity spikes (jerky motion)
✗ Velocity lags far behind command
✗ Velocity noise/oscillation (servo oscillating)
✗ Large difference between red and green
"""

# ============================================================================
# TROUBLESHOOTING CHECKLIST
# ============================================================================

"""
❌ Problem: ROS error / "rclpy not found"
✓ Solution: Set "use_ros": False to skip physical robot

❌ Problem: No /legs_feedback data recorded
✓ Solution: Check if your robot publishes feedback
          Joint name mapping might need adjustment
          Feedback is optional - script still works without it

❌ Problem: Comparison plot shows huge lag (phase shift)
✓ Solution: Try lower frequency first (0.5 Hz instead of 1.0 Hz)
          Check servo gains (kp, kd)
          Verify network latency on ROS

❌ Problem: Green and red lines don't match
✓ Solution: This is EXPECTED! You're trying to find these differences!
          Large gap = large sim-to-real gap = need to adjust sim params
          This is the whole point of the script

❌ Problem: Physical robot doesn't respond to commands
✓ Solution: Check: ros2 topic list (should see /legs_command)
          Check: Is robot powered on?
          Check: Are joint indices correct?
          Try: python nubiv6_playground.py (to test ROS setup)

❌ Problem: Simulation crashes
✓ Solution: Use smaller amplitude first (30° instead of 45°)
          Use slower frequency (0.5 Hz instead of 1 Hz)
          Check: Do you have Genesis installed? (import genesis)
          Set sim_show_viewer = True to debug visually

❌ Problem: Can't find saved data files
✓ Solution: Check: ls sim_to_real_data/
          Should see bridge_data_*.pkl files
          Make sure script completed (check "COMPLETED" message)
"""

# ============================================================================
# PARAMETER TUNING GUIDE
# ============================================================================

"""
If you see LAG (red/green line delayed from blue):
─────────────────────────────────────────────────
Issue: Servo response slow
Try:
  1. Lower frequency to 0.5 Hz (easier to follow slow motion)
  2. Reduce amplitude to 30° (less to move)
  3. Increase servo gains in nubiv6_env.py:
     - self.herk_Kp (currently 50.8)
     - self.herk_Kd (currently 0.13)
  4. Check pTime_ms (currently 35ms) - shorter = faster response


If you see OVERSHOOT (red/green goes past blue):
────────────────────────────────────────────────
Issue: Servo overshoots target, oscillates
Try:
  1. Increase frequency to 2 Hz (tests damping)
  2. Increase damping (Kd) in nubiv6_env.py
  3. Decrease proportional gain (Kp)
  4. Increase pTime_ms to slow down trajectory


If you see OSCILLATION (ringing around command):
─────────────────────────────────────────────────
Issue: Servo unstable at this frequency
Try:
  1. Reduce frequency (oscillation usually at high freq)
  2. Increase damping (Kd)
  3. Reduce gains overall
  4. Check for mechanical play/backlash in joints


If RED and GREEN are VERY DIFFERENT:
────────────────────────────────────
This is the goal! You want to find and understand this gap.

Analyze the difference:
  - Does physical lag more? → Network latency
  - Does physical overshoot more? → Different servo response
  - Different oscillation? → Friction/friction model mismatch
  
Suggestion: Adjust simulation parameters (friction, joint damping) to match
"""

# ============================================================================
# DATA ANALYSIS PYTHON SCRIPT
# ============================================================================

"""
# Load and analyze results manually:

import pickle
import numpy as np

# Load data
with open('sim_to_real_data/bridge_data_20260522_143015.pkl', 'rb') as f:
    data = pickle.load(f)

# Access components
commands = data['commands']
time_array = data['time_array']
sim_pos = data['sim_responses']['positions']
phys_pos = np.array(data['physical_responses']['feedback_positions'])[:, 11]

# Calculate metrics
position_error_sim = np.mean(np.abs(commands - sim_pos))
position_error_phys = np.mean(np.abs(commands - phys_pos))

print(f"Simulation MSE: {position_error_sim:.6f} rad")
print(f"Physical MSE: {position_error_phys:.6f} rad")
print(f"Sim-to-Real Gap: {position_error_phys - position_error_sim:.6f} rad")

# Find max tracking error
max_sim_error = np.max(np.abs(commands - sim_pos))
max_phys_error = np.max(np.abs(commands - phys_pos))

print(f"Max simulation error: {max_sim_error:.6f} rad ({np.rad2deg(max_sim_error):.2f}°)")
print(f"Max physical error: {max_phys_error:.6f} rad ({np.rad2deg(max_phys_error):.2f}°)")
"""

# ============================================================================
# EXPECTED RESULTS
# ============================================================================

"""
For a well-tuned servo on a 1 Hz, 45° sine wave:

SIMULATION (ideal):
  - Position tracking error < 0.05 rad (3°)
  - Smooth response, no oscillation
  - Velocity tracks commanded velocity profile

PHYSICAL (realistic):
  - Position tracking error 0.05-0.15 rad (3-9°)
  - Slight lag at peaks
  - May have minor oscillation after peaks
  - Smoother than jagged due to servo filtering

SIM-TO-REAL GAP:
  - Expected difference: 5-10% of amplitude
  - If > 20%, investigate differences in:
    - Friction (static vs dynamic)
    - Damping/stiffness
    - Servo control parameters
    - Communication latency
"""

# ============================================================================
# NEXT STEPS AFTER FIRST TEST
# ============================================================================

"""
✓ Step 1: Run default test
  → Confirms setup works
  → Gives baseline sim-to-real gap

✓ Step 2: Test different frequencies
  → Identifies servo bandwidth
  → Finds resonance frequencies

✓ Step 3: Test different joints
  → See if all joints respond similarly
  → Find outliers (joints with unusual behavior)

✓ Step 4: Test with gravity
  → More realistic conditions
  → Reveals gravity compensation needs

✓ Step 5: Sweep amplitudes
  → Find linear operating region
  → Identify saturation points

✓ Step 6: Adjust simulation parameters
  → Try different friction models
  → Try different joint stiffness
  → Match physics to real behavior

✓ Step 7: Create deployment config
  → Keep working parameters documented
  → Ready for actual robot training
"""

if __name__ == "__main__":
    print(__doc__)
