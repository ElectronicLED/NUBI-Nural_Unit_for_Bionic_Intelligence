# NUBI-Nural_Unit_for_Bionic_Intelligence
Born from the ancient ground, built for the future

## Overview
The **NUBI** project aims to develop a robust, adaptive, and generalizable control system for robotic agents using **Reinforcement Learning (RL)**.

This specific branch, reinforcement_learning, contains the primary codebase for developing, training, and testing the neural networks that serve as the intelligence unit for the system. We focus on training agents to perform complex motor tasks, learn from errors, and adapt to varying environmental conditions.

## Key Goal
To move beyond simple scripted movements and create a truly intelligent bionic unit capable of complex, goal-oriented behavior using state-of-the-art RL algorithms.

## Expexted problems
#### 1. OpenGL.error.Error: Attempt to retrieve context when no valid context
Solution:
https://github.com/Genesis-Embodied-AI/Genesis/issues/609

```
export MUJOCO_GL=glx
export PYOPENGL_PLATFORM=glx
```

#### 2. Robot collides with itself
solution:
go to ```~/.local/lib/python3.10/site-packages/genesis/options```
in a file called ```solvers.py```
in the class called ```RigidOptions```
set default ```enable_self_collision: bool = True```

this is a temperoary solution until I figure out how to set the options for each instance as it is created