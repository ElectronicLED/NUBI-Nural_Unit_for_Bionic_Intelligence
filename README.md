# NUBI-Nural_Unit_for_Bionic_Intelligence
Born from the ancient ground, built for the future

## Expexted errors
#### 1. OpenGL.error.Error: Attempt to retrieve context when no valid context
Solution:
https://github.com/Genesis-Embodied-AI/Genesis/issues/609

```
export MUJOCO_GL=glx
export PYOPENGL_PLATFORM=glx
```