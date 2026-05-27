# 🚀 SIM-TO-REAL BRIDGE - Complete Package

## 📋 Files Created

| File | Purpose | Size | Read Time |
|------|---------|------|-----------|
| **sim_to_real_bridge.py** | Main executable script | ~20KB | 10 min |
| **SIM_TO_REAL_SETUP_GUIDE.md** | Getting started guide | ~10KB | 10 min |
| **SIM_TO_REAL_README.md** | Complete documentation | ~15KB | 20 min |
| **BRIDGE_EXAMPLES.py** | 7 example configurations | ~12KB | 5 min |
| **QUICK_REFERENCE.py** | Cheat sheet & troubleshooting | ~15KB | 5 min |
| **SIM_TO_REAL_INDEX.md** | This file | - | 3 min |

---

## ⚡ Quick Start (Choose One)

### Option A: I Want to Run It Now (2 minutes)
```bash
cd /home/nour/NUBI-Nural_Unit_for_Bionic_Intelligence/NUBI_V6
python3 sim_to_real_bridge.py
```
→ Runs with all defaults, generates comparison plot

### Option B: I Want to Understand First (15 minutes)
Read in this order:
1. **SIM_TO_REAL_SETUP_GUIDE.md** - Overview and getting started
2. **SIM_TO_REAL_README.md** - Full feature documentation  
3. **BRIDGE_EXAMPLES.py** - See example configurations

Then run:
```bash
python3 sim_to_real_bridge.py
```

### Option C: I Want a Specific Configuration (5 minutes)
1. Find your use case in **BRIDGE_EXAMPLES.py**
2. Copy the CONFIG dict
3. Paste into **sim_to_real_bridge.py**
4. Run script

---

## 📚 Documentation Map

```
START HERE
    ↓
┌─────────────────────────────────────┐
│ SIM_TO_REAL_SETUP_GUIDE.md         │ ← Read this first!
│ (5-15 min)                          │   - What was created
│ - Quick overview                    │   - How to run it
│ - Getting started in 5 minutes      │   - First test workflow
└──────────────────┬──────────────────┘
                   ↓
        WANT TO USE THE SCRIPT?
        ↙              ↓              ↖
    (Just run)   (Customize)    (Deep dive)
       ↓               ↓               ↓
   python3     BRIDGE_      SIM_TO_REAL_
   sim_to_     EXAMPLES.py   README.md
   real_       (5 min)       (20 min)
   bridge.py   ← Config      ← Full
   (2 min)     examples      reference
      ↓               ↓               ↓
   DONE!        Modify &       Understand
   Plot         Run            everything
   generated    (5 min)        (20 min)
                                   ↓
                            QUICK_REFERENCE.py
                            (troubleshooting,
                             tips, analysis)
```

---

## 🎯 What This System Does

### The Problem
Training RL policies in simulation but deploying on real hardware creates a "sim-to-real gap" - the robot doesn't behave the same way in reality as it does in simulation.

### The Solution
This script helps you:
1. **Test** identical sine wave commands on both physical robot and simulation
2. **Record** how each system responds to those commands
3. **Compare** responses visually on a plot
4. **Analyze** the differences (lag, overshoot, oscillation, etc.)
5. **Iterate** on simulation parameters to close the gap

### The Output
For each test, you get:
- **PNG plot** showing command vs physical vs simulated response
- **Pickle data** with all raw numbers for analysis
- **Console output** with progress and diagnostics

---

## 🔄 How to Use It

### One-Time Setup
```bash
# No special setup needed! Just run:
python3 sim_to_real_bridge.py
```

### Typical Workflow

```
Day 1: Characterize Robot
├─ Test LAnkle_pitch at 1 Hz (default config)
├─ Test RHip_roll at 0.5 Hz (slower)
├─ Test RKnee_pitch at 2 Hz (faster)
└─ → Understand servo bandwidth

Day 2: Identify Gap
├─ Compare plots - notice differences
├─ Measure lag, overshoot, oscillation
├─ Document key issues
└─ → Know what needs fixing

Day 3: Tune Simulation
├─ Adjust Herkulex parameters in nubiv6_env.py
├─ Use replay mode to test without physical robot
├─ Iterate quickly (no ROS overhead)
└─ → Close the sim-to-real gap

Day 4: Validate
├─ Physical test matches simulation
├─ Same servo behavior in both
└─ → Ready for RL training!
```

---

## 📊 Key Features

| Feature | Details |
|---------|---------|
| **Sine Wave Generation** | Configurable frequency (Hz) and amplitude (degrees) |
| **Physical Robot Control** | Sends via ROS `/legs_command` at 50Hz |
| **Feedback Recording** | Records from `/legs_feedback` topic (optional) |
| **Simulation** | Uses Genesis with identical commands |
| **Visualization** | Matplotlib plots with command + physical + simulated |
| **Data Persistence** | Saves as pickle for later analysis |
| **Replay Mode** | Re-run simulation without physical robot |
| **Joint Selection** | Test any of 12 joints (6 per leg) |
| **Configuration** | Simple Python dict at top of script |

---

## 🎮 Configuration Parameters

Edit these in `sim_to_real_bridge.py`:

```python
CONFIG = {
    # Which joint to test
    "target_joint_idx": 11,              # 0-11
    "target_joint_name": "LAnkle_pitch", # For reference
    
    # Sine wave shape
    "sine_frequency_hz": 1.0,            # 0.1 to 5.0
    "sine_amplitude_deg": 45.0,          # 10 to 90
    "test_duration_s": 3.0,              # 1 to 30
    
    # Control rate
    "control_frequency_hz": 50.0,        # Always 50 for compatibility
    
    # ROS
    "use_ros": True,                     # False to skip physical
    
    # Simulation
    "sim_show_viewer": False,            # True to see Genesis viewer
    "sim_gravity": (0.0, 0.0, 0.0),      # Gravity vector
    
    # Output
    "data_dir": "sim_to_real_data",      # Where to save files
}
```

---

## 📈 Interpreting Results

After running, you'll see a comparison plot with:

**Top graph (Position):**
- 🔵 Blue = Your commanded sine wave
- 🔴 Red = Simulated joint response  
- 🟢 Green = Physical robot response

**Bottom graph (Velocity):**
- 🔵 Blue = Command velocity
- 🔴 Red = Simulated velocity
- 🟢 Green = Physical velocity

**Good results:**
- Red and green lines closely follow blue line
- Minimal phase lag
- Smooth, no jerky oscillations

**What you're looking for:**
- How much does physical lag behind simulation?
- Does physical overshoot more?
- Is there oscillation in physical but not simulation?
- Can you fix it with parameter tuning?

---

## 💾 Data Storage

All results saved in `sim_to_real_data/` directory:

```
sim_to_real_data/
├── bridge_data_20260522_143015.pkl      # Full test data (timestamp 1)
├── bridge_data_20260522_143045.pkl      # Full test data (timestamp 2)
├── comparison_20260522_143015.png       # Comparison plot (timestamp 1)
└── comparison_20260522_143045.png       # Comparison plot (timestamp 2)
```

**To reload and analyze:**
```python
import pickle

with open('sim_to_real_data/bridge_data_20260522_143015.pkl', 'rb') as f:
    data = pickle.load(f)

commands = data['commands']
sim_positions = data['sim_responses']['positions']
physical_positions = data['physical_responses']['feedback_positions']
```

---

## 🛠️ Advanced Usage

### Replay Previous Test (No Physical Robot)
```bash
python3 sim_to_real_bridge.py replay
```
- Selects a previous test
- Re-runs simulation only
- Useful for trying different gravity/parameters

### Batch Testing Different Joints
```python
# Add this to script:
for joint_idx in [1, 3, 10, 11]:
    CONFIG["target_joint_idx"] = joint_idx
    main()
```

### Data Analysis
```python
import numpy as np
from scipy import signal

# Load data
data = pickle.load(open('sim_to_real_data/bridge_data_*.pkl', 'rb'))

# Compute tracking error
commands = data['commands']
sim_pos = data['sim_responses']['positions']
error = np.mean(np.abs(commands - sim_pos))

print(f"Position tracking error: {error:.6f} rad ({np.rad2deg(error):.2f}°)")
```

---

## ⚠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'genesis'"
**Solution:** Install Genesis
```bash
pip install genesis-world
```

### Issue: "ROS not available. Skipping physical robot testing."
**This is normal.** Script will run simulation-only. Set `"use_ros": False` to suppress message.

### Issue: Physical robot doesn't respond
**Check:**
```bash
ros2 topic list | grep legs    # Should show /legs_command
ros2 node list                 # Should show robot node
```

### Issue: Plot doesn't display
**Try:**
```bash
pip install matplotlib PyQt5
```

→ See **QUICK_REFERENCE.py** for more troubleshooting

---

## 📖 Reading Guide by Use Case

**"I just want to run it"**
→ Run script directly, view PNG

**"I want to understand what it does"**
→ Read: SIM_TO_REAL_SETUP_GUIDE.md

**"I want to customize it"**
→ Read: BRIDGE_EXAMPLES.py, then edit CONFIG

**"I want to understand the physics"**
→ Read: SIM_TO_REAL_README.md (full section)

**"I'm having problems"**
→ See: QUICK_REFERENCE.py (troubleshooting)

**"I want to analyze the data"**
→ Use the pickle files with custom Python scripts

---

## 🔗 File Relationships

```
sim_to_real_bridge.py (MAIN SCRIPT)
├── Uses: nubiv6_train.py (get_cfgs)
├── Uses: nubiv6_env.py (NubiEnv class)
├── Imports: genesis, torch, matplotlib, numpy, pickle
└── Creates: sim_to_real_data/ directory
    ├── bridge_data_*.pkl (data storage)
    └── comparison_*.png (visualization)

DOCUMENTATION
├── SIM_TO_REAL_SETUP_GUIDE.md (START HERE!)
├── SIM_TO_REAL_README.md (COMPREHENSIVE)
├── BRIDGE_EXAMPLES.py (CONFIGURATIONS)
├── QUICK_REFERENCE.py (CHEAT SHEET)
└── SIM_TO_REAL_INDEX.md (THIS FILE)
```

---

## ✅ Verification Checklist

- [x] Script syntax validated (no errors)
- [x] All imports available in your environment
- [x] Default configuration tested and working
- [x] ROS integration ready (if ROS available)
- [x] Simulation integration ready (Genesis)
- [x] Data save/load working
- [x] Plotting functions ready
- [x] Documentation complete

**Status:** ✅ Ready to Use

---

## 🎓 Learning Path

**Level 1: Just Run It** (2 min)
```bash
python3 sim_to_real_bridge.py
```

**Level 2: Customize Joint** (5 min)
Edit `target_joint_idx` in CONFIG, run again

**Level 3: Change Wave Parameters** (5 min)
Modify `sine_frequency_hz`, `sine_amplitude_deg`, run again

**Level 4: Analyze Results** (10 min)
Load pickle file, compute metrics, compare plots

**Level 5: Tune Simulation** (30 min)
Adjust `herk_Kp`, `herk_Kd` in nubiv6_env.py, use replay mode

**Level 6: Full Workflow** (2+ hours)
Characterize robot, identify gaps, iterate on parameters

---

## 🎯 Success Milestones

- [x] Script created and verified
- [ ] Run first test with defaults
- [ ] Compare physical vs simulated responses
- [ ] Identify 1-2 key differences
- [ ] Adjust simulation parameters
- [ ] Reduce sim-to-real gap by 50%
- [ ] Achieve <5% tracking error

---

## 📞 Support

**Quick answers:**
→ QUICK_REFERENCE.py

**Understanding features:**
→ SIM_TO_REAL_README.md

**Configuration examples:**
→ BRIDGE_EXAMPLES.py

**Getting started:**
→ SIM_TO_REAL_SETUP_GUIDE.md

---

## 🚀 Ready to Bridge Your Sim-to-Real Gap!

**Next Step:** Read **SIM_TO_REAL_SETUP_GUIDE.md** (10 min) then run the script!

```bash
python3 sim_to_real_bridge.py
```

Good luck! 🎉
