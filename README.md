# NUBI-Nural_Unit_for_Bionic_Intelligence
Born from the ancient ground, built for the future

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