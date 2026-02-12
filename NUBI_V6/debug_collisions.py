import genesis as gs
from nubiv6_env import NubiEnv
from nubiv6_train import get_cfgs
import torch

# Link names extracted from your NUBI_V4.urdf in order
LINK_NAMES = [
    'base_link', #0
    'RPelvis',#1
    'RHip',#2
    'RFemur',#3
    'RTibia',
    'RAnkle',
    'RFoot',
    'LPelvis',
    'LHip',
    'LFemur',
    'LTibia',
    'LAnkle',
    'LFoot',
    'chest',
    'RShoulder',
    'RHumerus',
    'RForearm',
    'LShoulder',
    'LHumerus',
    'LForearm'     # 19
]


class DebugNubiEnv(NubiEnv):
    """
    A subclass of NubiEnv that forces collision checking ON
    regardless of what is in the original file.
    """
    def __init__(self, num_envs, env_cfg, obs_cfg, reward_cfg, command_cfg):
        # We must copy the init logic to force enable_collision=True
        self.num_envs = num_envs
        self.dt = 0.02
        self.env_cfg = env_cfg
        
        # Initialize Scene with Collision ENABLED
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.dt, substeps=2),
            rigid_options=gs.options.RigidOptions(
                dt=self.dt,
                constraint_solver=gs.constraint_solver.Newton,
                enable_collision=True,       # <--- FORCED ON
                enable_joint_limit=True,
            ),
            show_viewer=True, # Enable viewer to see the freeze
        )
        
        # Add plain
        self.scene.add_entity(gs.morphs.Plane())

        # Add robot
        self.base_init_pos = torch.tensor(env_cfg["base_init_pos"], device=gs.device)
        self.base_init_quat = torch.tensor(env_cfg["base_init_quat"], device=gs.device)
        
        self.robot = self.scene.add_entity(
            gs.morphs.URDF(
                file="NUBI_V6.urdf",
                pos=self.base_init_pos.cpu().numpy(),
                quat=self.base_init_quat.cpu().numpy(),
            ),
        )
        
        self.scene.build(n_envs=num_envs)
        
        # (Skip the rest of the full init for this simple debug check)

def main():
    gs.init(logging_level="warning")
    
    # Load configuration
    env_cfg, obs_cfg, reward_cfg, command_cfg = get_cfgs()
    
    # Initialize Debug Environment
    print("Initializing environment...")
    env = DebugNubiEnv(1, env_cfg, obs_cfg, reward_cfg, command_cfg)
    
    while True: 
        # Step once to settle physics engine slightly
        print("Stepping simulation...")
        env.scene.step()
        
        # Detect Collisions
        # genesis.Entity.detect_collision() returns a list of contacts.
        # We inspect the raw return.
        collisions = env.robot.detect_collision()
        print(collisions)
        
        print("\n" + "="*40)
        print(f"FOUND {len(collisions)} COLLISIONS")
        print("="*40)
        
        if len(collisions) == 0:
            print("No self-collisions detected! (Did you disable them in the URDF?)")
        else:
            for i, col in enumerate(collisions):
                # col is typically [link_idx_A, link_idx_B, ...]
                # Note: Your original code filtered 'if x[0]!=0'. 
                # If x[0] is the link index, you were ignoring collisions with the base_link!
                
                idx_a = int(col.link_a) if hasattr(col, 'link_a') else int(col[0])
                idx_b = int(col.link_b) if hasattr(col, 'link_b') else int(col[1])
                
                name_a = LINK_NAMES[idx_a] if 0 <= idx_a < len(LINK_NAMES) else f"Unknown({idx_a})"
                name_b = LINK_NAMES[idx_b] if 0 <= idx_b < len(LINK_NAMES) else f"Unknown({idx_b})"
                
                print(f"Collision {i+1}: {name_a} <--> {name_b}")

        if input("q to exit, any other key to continue: ") == 'q':
            break
    

if __name__ == "__main__":
    main()