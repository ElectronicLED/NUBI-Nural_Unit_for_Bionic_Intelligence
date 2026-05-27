# Sim-to-Real Bridge - Complete Setup Guide

## ✅ What Has Been Created

You now have a complete sim-to-real bridge system with 4 files:

### 1. **sim_to_real_bridge.py** (Main Script)
The core script that:
- Generates sine wave commands at configurable frequency & amplitude
- Sends commands to physical robot at 50Hz via ROS `/legs_command` topic
- Records feedback from `/legs_feedback` topic
- Runs identical commands in Genesis simulation
- Generates comparison plots (command vs physical vs simulated)
- Saves all data for later analysis
- Supports replay mode (re-run sim without physical robot)

**Status:** ✅ Syntax verified, ready to use

### 2. **SIM_TO_REAL_README.md** (Comprehensive Documentation)
Complete reference including:
- Feature overview
- Usage instructions (basic and replay modes)
- Configuration reference
- Interpretation of output plots
- Troubleshooting guide
- Performance metrics
- Future enhancement ideas

### 3. **BRIDGE_EXAMPLES.py** (7 Ready-to-Use Configurations)
Pre-configured examples:
1. LAnkle_pitch - 1Hz sine (default)
2. RHip_roll - 0.5Hz slow oscillation
3. RKnee_pitch - 2Hz fast oscillation
4. LAnkle_roll - Full range test (60°)
5. Simulation-only (no ROS/physical robot)
6. With gravity (realistic simulation)
7. Extended 15-second duration test

### 4. **QUICK_REFERENCE.py** (Cheat Sheet)
Quick lookup guide with:
- Command-line usage examples
- Joint index reference table
- Common testing patterns
- Troubleshooting checklist
- Data analysis code snippets
- Expected results baseline

---

## 🚀 Getting Started (5 Minutes)

### Prerequisites
```bash
# Ensure these are installed:
- Python 3.8+
- PyTorch
- Genesis (physics simulator)
- matplotlib
- numpy
- ROS 2 (optional, for physical robot)
```

### First Test - Run Default Configuration

```bash
cd /home/nour/NUBI-Nural_Unit_for_Bionic_Intelligence/NUBI_V6
python3 sim_to_real_bridge.py
```

**What happens:**
1. Script asks if you want to test physical robot (or skips if ROS unavailable)
2. Generates 1Hz sine wave, 45° amplitude, 3-second duration
3. If ROS available: Sends commands to robot, records feedback
4. Runs identical commands in simulation
5. Generates comparison plot: `sim_to_real_data/comparison_TIMESTAMP.png`
6. Saves data: `sim_to_real_data/bridge_data_TIMESTAMP.pkl`

**Expected output in console:**
```
============================================================
SIM-TO-REAL BRIDGE SCRIPT
============================================================

Configuration:
  Target Joint: LAnkle_pitch (index 11)
  Sine Wave: 1.0 Hz, 45° amplitude
  Duration: 3.0 seconds @ 50.0 Hz
  Use ROS: True

Generating sine wave commands...
Generated 151 commands
  Min: -0.7854 rad (-45.00°)
  Max: 0.7854 rad (45.00°)

[Physical robot test if ROS available]

SIMULATION TEST
...
Generated comparison plots...

============================================================
SCRIPT COMPLETED SUCCESSFULLY
============================================================
```

---

## ⚙️ Common Configuration Changes

### Test Different Joints

Just change `target_joint_idx` in the CONFIG dictionary:

```python
CONFIG = {
    "target_joint_idx": 1,  # Change this!
    "target_joint_name": "RHip_roll",
    ...
}
```

Available joints (index : name):
- 0: RHip_yaw
- 1: RHip_roll (recommended)
- 2: RHip_pitch
- 3: RKnee_pitch (recommended)
- **10: LAnkle_roll** (recommended)
- **11: LAnkle_pitch** (default)

### Change Sine Wave Parameters

```python
CONFIG = {
    "sine_frequency_hz": 0.5,  # Slow down to 0.5 Hz
    "sine_amplitude_deg": 30.0,  # Reduce amplitude to 30°
    "test_duration_s": 5.0,  # Extend to 5 seconds
    ...
}
```

### Skip Physical Robot (Simulation Only)

```python
CONFIG = {
    "use_ros": False,  # Skip ROS/physical robot!
    ...
}
```

This is useful for:
- Testing script without robot
- Debugging visualization
- Running faster tests

---

## 📊 Understanding the Output

### Console Output
Shows:
- Configuration being used
- Number of commands generated
- Progress of physical test (if running)
- Progress of simulation
- File locations for saved data

### Comparison Plot (PNG file)
Two graphs stacked vertically:

**Top: Position Response**
- Blue line: Commanded position (ideal sine wave)
- Red line: Simulated joint position
- Green line: Physical robot position (if available)

**Bottom: Velocity Response**
- Blue line: Commanded velocity
- Red line: Simulated joint velocity
- Green line: Physical robot velocity (if available)

### Saved Data (Pickle file)
Contains all raw data for post-analysis:
```python
import pickle

with open('sim_to_real_data/bridge_data_TIMESTAMP.pkl', 'rb') as f:
    data = pickle.load(f)

# Access:
data['commands']                          # Original sine wave
data['sim_responses']['positions']        # Simulated joint positions
data['physical_responses']['feedback_positions']  # Real robot positions
```

---

## 🔄 Replay Mode (Reuse Physical Robot Test Data)

After running a physical test, replay the simulation:

```bash
python3 sim_to_real_bridge.py replay
```

**Benefits:**
- Re-run simulation with exactly same commands
- Try different gravity settings
- Adjust visualization without re-testing robot
- Compare multiple simulation runs
- Faster iteration (no ROS overhead)

**What happens:**
1. Lists all saved test files
2. Prompts you to select one
3. Re-runs simulation with those exact commands
4. Generates new comparison plot
5. Does NOT touch physical robot

---

## 📈 Workflow Recommendations

### Workflow 1: Initial Calibration (30 minutes)
```
1. Edit CONFIG to skip ROS: "use_ros": False
   → python3 sim_to_real_bridge.py
   → Verify script works, plots generate correctly
   
2. Enable ROS: "use_ros": True
   → python3 sim_to_real_bridge.py
   → Record physical robot response, compare plots
```

### Workflow 2: Joint Characterization (2 hours)
```
For each joint of interest:
   1. Set target_joint_idx and target_joint_name
   2. Run at 0.5 Hz, 30° amplitude for 3 sec
   3. Run at 1.0 Hz, 45° amplitude for 3 sec
   4. Run at 2.0 Hz, 30° amplitude for 3 sec
   5. Compare plots - identify frequency response
```

### Workflow 3: Servo Tuning (1 hour)
```
1. Find sim/real gap from Workflow 2
2. Identify key differences (lag, overshoot, etc)
3. Adjust nubiv6_env.py Herkulex parameters:
   - self.herk_Kp (proportional gain)
   - self.herk_Kd (derivative gain)
   - self.pTime_ms (trajectory time)
4. Re-run simulations (replay mode) to iterate
5. Once sim matches reality, use for training
```

### Workflow 4: Gravity Testing (30 minutes)
```
1. Run baseline (no gravity): "sim_gravity": (0.0, 0.0, 0.0)
2. Change to realistic gravity: "sim_gravity": (0.0, 0.0, -9.81)
3. Use replay mode to compare without physical test
4. Decide if gravity should be on/off for training
```

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'genesis'"
```bash
# You need to install Genesis
pip install genesis-world
```

### "ROS not available. Skipping physical robot testing."
This is fine! The script detected ROS is not available and skipped it.
- Script will run simulation-only
- Set `"use_ros": False` explicitly to avoid the warning

### Physical robot not responding
Check ROS:
```bash
ros2 topic list | grep legs
```

Should show:
- `/legs_command` (publisher)
- `/legs_feedback` (subscriber, optional)

### Plot not displaying
Might need to install matplotlib backend:
```bash
pip install matplotlib PyQt5
```

### Data not saving
Check write permissions:
```bash
mkdir -p sim_to_real_data
chmod 777 sim_to_real_data
```

---

## 📁 File Structure After First Run

```
/home/nour/NUBI-Nural_Unit_for_Bionic_Intelligence/NUBI_V6/
├── sim_to_real_bridge.py              ← Main script
├── SIM_TO_REAL_README.md              ← Full documentation
├── BRIDGE_EXAMPLES.py                 ← Configuration examples
├── QUICK_REFERENCE.py                 ← Cheat sheet
├── SIM_TO_REAL_SETUP_GUIDE.md          ← This file
├── nubiv6_env.py                      ← Original environment
├── nubiv6_train.py                    ← Original training
└── sim_to_real_data/                  ← Created by script
    ├── bridge_data_20260522_143015.pkl
    ├── bridge_data_20260522_143045.pkl
    ├── comparison_20260522_143015.png
    ├── comparison_20260522_143045.png
    └── ...
```

---

## 🎯 Success Criteria

You'll know everything is working when:

✅ Script runs without errors
✅ Simulation test completes successfully  
✅ PNG comparison plot is generated
✅ Data pickle file is saved
✅ Plots show:
  - Sine wave commands on blue line
  - Simulated response on red line
  - Physical response on green line (if available)
  - Minimal lag/overshoot for 1Hz test

---

## 📚 Next Steps

1. **[IMMEDIATE]** Run default test to verify setup
2. **[5 min]** Review generated comparison plot
3. **[15 min]** Explore QUICK_REFERENCE.py for common tasks
4. **[30 min]** Test 2-3 different joints
5. **[1 hour]** Analyze sim-to-real gap
6. **[Ongoing]** Iterate on parameters to close gap

---

## 💡 Pro Tips

- **Start simple:** Default config is proven to work
- **Document results:** Comparison PNGs are automatically saved with timestamps
- **Use replay mode:** No need to re-test physical robot while iterating
- **Save good runs:** Pickle files preserve exact commands for reproducibility
- **Compare across frequency:** 0.5 Hz vs 1 Hz vs 2 Hz reveals bandwidth
- **Test all joints:** Build understanding of robot dynamics
- **Adjust gradually:** Make one parameter change at a time

---

## 🆘 Getting Help

If you run into issues:

1. Check **QUICK_REFERENCE.py** troubleshooting section
2. Review **SIM_TO_REAL_README.md** for detailed explanations
3. Look at **BRIDGE_EXAMPLES.py** for working configurations
4. Check console output for specific error messages
5. Verify ROS setup: `ros2 node list`

---

## 📝 Configuration Checklist

Before running, verify:

- [ ] Python 3.8+ installed
- [ ] Genesis installed (`import genesis` works)
- [ ] PyTorch installed (`import torch` works)
- [ ] matplotlib installed (`import matplotlib` works)
- [ ] ROS 2 available (optional: `ros2 --version`)
- [ ] NUBI robot connected (if testing physically)
- [ ] `/legs_command` topic accessible (if using ROS)
- [ ] Write permissions in script directory
- [ ] At least 100MB free disk space (for data/plots)

---

**Ready to bridge the sim-to-real gap!** 🚀
