import torch
import math
import genesis as gs
from genesis.utils.geom import quat_to_xyz, transform_by_quat, inv_quat, transform_quat_by_quat


# Function to create a random numbors to send commands to the robot
def gs_rand_float(lower, upper, shape, device):
    return (upper - lower) * torch.rand(size=shape, device=device) + lower


class NubiEnv:
    def __init__(self, num_envs, env_cfg, obs_cfg, reward_cfg, command_cfg, show_viewer=False):
        self.num_envs = num_envs
        self.num_obs = obs_cfg["num_obs"]
        self.num_privileged_obs = None
        self.num_actions = env_cfg["num_actions"]
        self.num_commands = command_cfg["num_commands"]
        self.device = gs.device

        self.simulate_action_latency = True  # there is a 1 step latency on real robot
        self.dt = 0.02  # control frequency on real robot is 50hz
        self.sim_dt = 0.004 #Physics and PD control frequency (1000Hz)
        self.control_substeps = int(self.dt / self.sim_dt) # 20 steps per RL action
        self.max_episode_length = math.ceil(env_cfg["episode_length_s"] / self.dt)

        self.env_cfg = env_cfg
        self.obs_cfg = obs_cfg
        self.reward_cfg = reward_cfg
        self.command_cfg = command_cfg

        self.obs_scales = obs_cfg["obs_scales"]
        self.reward_scales = reward_cfg["reward_scales"]


        # set gravity from env_cfg if provided, else default
        gravity = self.env_cfg.get("gravity", (0.0, 0.0, -9.81))
        # create scene
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.sim_dt, substeps=1, gravity=gravity),
            viewer_options=gs.options.ViewerOptions(
                max_FPS=int(1.25 / self.dt),
                camera_pos=(-2.0, 1.5, 1.0),
                camera_lookat=(0.0, 0.0, 0.5),
                camera_fov=40,
            ),
            vis_options=gs.options.VisOptions(
                show_world_frame=True, 
                shadow=False,
                plane_reflection=False,
                show_link_frame=False,
                background_color=(0.04, 0.08, 0.12),
                ambient_light = (0.1, 0.1, 0.1),
            ),
            rigid_options=gs.options.RigidOptions(
                dt=self.sim_dt,
                constraint_solver=gs.constraint_solver.Newton,
                enable_collision=True,
                enable_joint_limit=True,
                enable_self_collision=True,
            ),
            show_viewer=show_viewer,
        )

        # add plain
        self.scene.add_entity(
            gs.morphs.Plane()
        )

        # add robot
        self.base_init_pos = torch.tensor(self.env_cfg["base_init_pos"], device=gs.device)
        self.base_init_quat = torch.tensor(self.env_cfg["base_init_quat"], device=gs.device)
        self.inv_base_init_quat = inv_quat(self.base_init_quat)
        self.robot = self.scene.add_entity(
            gs.morphs.URDF(
                file="NUBI_V6.urdf",
                pos=self.base_init_pos.cpu().numpy(),
                quat=self.base_init_quat.cpu().numpy(),
            ),
        )

        # build
        self.scene.build(n_envs=num_envs)

        # names to indices (use local dof indices for per-joint control)
        self.motors_dof_idx = [self.robot.get_joint(name).dof_idx_local for name in self.env_cfg["joint_names"]]

        # Initialize all joints to default positions immediately after build
        # This prevents Genesis's default initialization (±π) from being seen in the first step
        self.default_dof_pos = torch.tensor(
            [self.env_cfg["default_joint_angles"][name] for name in self.env_cfg["joint_names"]],
            device=gs.device,
            dtype=gs.tc_float,
        )
        self.robot.set_dofs_position(
            self.default_dof_pos.unsqueeze(0).repeat(num_envs, 1),
            self.motors_dof_idx
        )

        self.actions = torch.zeros((self.num_envs, self.num_actions), device=gs.device, dtype=gs.tc_float)
        self.last_actions = torch.zeros_like(self.actions)
        self.dof_pos = torch.zeros_like(self.actions)
        self.dof_vel = torch.zeros_like(self.actions)
        self.last_dof_vel = torch.zeros_like(self.actions)
        self.base_pos = torch.zeros((self.num_envs, 3), device=gs.device, dtype=gs.tc_float)
        self.base_quat = torch.zeros((self.num_envs, 4), device=gs.device, dtype=gs.tc_float)

        # PD control parameters
        # self.robot.set_dofs_kp([self.env_cfg["kp"]] * self.num_actions, self.motors_dof_idx)
        # self.robot.set_dofs_kv([self.env_cfg["kd"]] * self.num_actions, self.motors_dof_idx)
        ###############################ChatGPT Added###############################
        # # 1. Disable internal PD (set to 0 so physics engine doesn't interfere)
        self.robot.set_dofs_kp([0.0] * self.num_actions, self.motors_dof_idx)
        self.robot.set_dofs_kv([0.0] * self.num_actions, self.motors_dof_idx)

        # # 2. Store your config gains for manual calculation
        # # We create tensors of shape (num_envs, num_actions) for easy multiplication later
        # self.kp = torch.tensor([self.env_cfg["kp"]] * self.num_actions, device=gs.device)
        # self.kd = torch.tensor([self.env_cfg["kd"]] * self.num_actions, device=gs.device)

        # # 3. Buffer to store previous target position (needed to calculate target velocity)
        # self.prev_target_dof_pos = torch.zeros((self.num_envs, self.num_actions), device=gs.device, dtype=gs.tc_float)
        # # Initialize it to the default pose
        # self.prev_target_dof_pos[:] = self.default_dof_pos

        # --- Herkulex DRS-0101 Sim-to-Real Parameters ---
        self.max_torque = 1.2  # Max physical torque in Nm
        self.pTime_ms = 35    # Target time for a full trajectory in milliseconds
        
        # Every tick is 11.2ms. We cast to int to mimic the microcontroller's discrete registers.
        self.pTime_ticks = int(self.pTime_ms / 11.2) if self.pTime_ms > 0 else 89
        
        # Genesis physics require time in SECONDS
        self.tick_s = 0.0112   
        
        # Total Play Time (T) in seconds
        self.T = self.pTime_ticks * self.tick_s
        
        # Acceleration time (t_acc) in seconds
        self.accel_ratio = 20.0  # 20% acceleration ratio
        self.t_acc = self.T * (self.accel_ratio / 100.0)
        # Raw values read directly from the Herkulex registers
        self.raw_Kp = 254.0
        self.raw_Kd = 6500.0
        
        # Scaling factors to convert Microcontroller Units to SI Units (Nm)
        # We start very small to prevent physics explosions.
        self.kp_scale = 0.2   # TODO Tune this
        self.kd_scale = 0.00002 # TODO Tune this
        
        # Final Gains used by Genesis
        self.herk_Kp = self.raw_Kp * self.kp_scale
        self.herk_Kd = self.raw_Kd * self.kd_scale
        self.herk_Kff = 0.1  # NEW: Velocity Feedforward Gain

        # State Tracking Tensors (Shape: [num_envs, num_actions])
        self.herk_goal_pos = torch.zeros((self.num_envs, self.num_actions), device=self.device, dtype=gs.tc_float)
        self.herk_start_pos = torch.zeros_like(self.herk_goal_pos)
        self.herk_time_elapsed = torch.zeros_like(self.herk_goal_pos)
        self.herk_current_pos = torch.zeros_like(self.herk_goal_pos)
        self.herk_current_vel = torch.zeros_like(self.herk_goal_pos)
        #######################################################################
        
        
        # Per-joint weights for similar_to_default reward (optional, defaults to 1.0 for all joints)
        if "similar_to_default_weights" in reward_cfg:
            self.similar_to_default_weights = torch.tensor(
                reward_cfg["similar_to_default_weights"],
                device=gs.device,
                dtype=gs.tc_float
            )
        else:
            self.similar_to_default_weights = torch.ones(self.num_actions, device=gs.device, dtype=gs.tc_float)
        
        # prepare reward functions and multiply reward scales by dt
        self.reward_functions, self.episode_sums = dict(), dict()
        for name in self.reward_scales.keys():
            self.reward_scales[name] *= self.dt
            self.reward_functions[name] = getattr(self, "_reward_" + name)
            self.episode_sums[name] = torch.zeros((self.num_envs,), device=gs.device, dtype=gs.tc_float)

        # initialize buffers
        self.base_lin_vel = torch.zeros((self.num_envs, 3), device=gs.device, dtype=gs.tc_float)
        self.base_ang_vel = torch.zeros((self.num_envs, 3), device=gs.device, dtype=gs.tc_float)
        self.projected_gravity = torch.zeros((self.num_envs, 3), device=gs.device, dtype=gs.tc_float)
        self.global_gravity = torch.tensor([0.0, 0.0, -1.0], device=gs.device, dtype=gs.tc_float).repeat(
            self.num_envs, 1
        )
        self.obs_buf = torch.zeros((self.num_envs, self.num_obs), device=gs.device, dtype=gs.tc_float)
        self.rew_buf = torch.zeros((self.num_envs,), device=gs.device, dtype=gs.tc_float)
        self.reset_buf = torch.ones((self.num_envs,), device=gs.device, dtype=gs.tc_int)
        self.episode_length_buf = torch.zeros((self.num_envs,), device=gs.device, dtype=gs.tc_int)
        self.commands = torch.zeros((self.num_envs, self.num_commands), device=gs.device, dtype=gs.tc_float)
        self.commands_scale = torch.tensor(
            [self.obs_scales["lin_vel"], self.obs_scales["lin_vel"], self.obs_scales["ang_vel"]],
            device=gs.device,
            dtype=gs.tc_float,
        )
        self.extras = dict()  # extra information for logging
        self.extras["observations"] = dict()
        # For alternating feet height reward
        self.last_rewarded_leg = torch.full((self.num_envs,), -1, dtype=torch.int, device=gs.device)  # -1: none, 0: right, 1: left
        #self.feet_height_threshold = self.reward_cfg["feet_height_target_difference"]  # default 3 cm

    def _resample_commands(self, envs_idx):
        self.commands[envs_idx, 0] = gs_rand_float(*self.command_cfg["lin_vel_x_range"], (len(envs_idx),), gs.device)
        self.commands[envs_idx, 1] = gs_rand_float(*self.command_cfg["lin_vel_y_range"], (len(envs_idx),), gs.device)
        self.commands[envs_idx, 2] = gs_rand_float(*self.command_cfg["ang_vel_range"], (len(envs_idx),), gs.device)

    def step(self, actions):

        # self.actions = torch.clip(actions, -self.env_cfg["clip_actions"], self.env_cfg["clip_actions"]) #sets a ceil and floor for actions
        # exec_actions = self.last_actions if self.simulate_action_latency else self.actions
        # target_dof_pos = exec_actions * self.env_cfg["action_scale"] + self.default_dof_pos
        # self.robot.control_dofs_position(target_dof_pos, self.motors_dof_idx)
        # self.scene.step()

        #################################ChatGPT Added###############################
        
        # 1. Calculate the new target positions from the RL policy
        # (Ensure self.default_dof_pos and self.action_scale are defined in your env)
        self.actions = torch.clip(actions, -self.env_cfg["clip_actions"], self.env_cfg["clip_actions"]) #sets a ceil and floor for actions
        exec_actions = self.last_actions if self.simulate_action_latency else self.actions

        target_dof_pos = exec_actions * self.env_cfg["action_scale"] + self.default_dof_pos

        # 2. Detect if the RL policy issued a NEW command
        # Using 1e-4 epsilon to ignore tiny floating-point noise from the neural net
        new_cmd_mask = torch.abs(target_dof_pos - self.herk_goal_pos) > 0.05

        # 3. Update trajectory state tensors where a new command was received
        self.herk_start_pos = torch.where(new_cmd_mask, self.herk_current_pos, self.herk_start_pos)
        self.herk_goal_pos = torch.where(new_cmd_mask, target_dof_pos, self.herk_goal_pos)
        self.herk_time_elapsed = torch.where(new_cmd_mask, torch.zeros_like(self.herk_time_elapsed), self.herk_time_elapsed)
        
        # 4. Advance time for the internal servo trajectory generator
        # self.herk_time_elapsed += self.dt
        # t = self.herk_time_elapsed

        # # 5. Calculate Trapezoidal Kinematics
        # D = self.herk_goal_pos - self.herk_start_pos
        # v_max = D / (self.T - self.t_acc)
        # accel = v_max / self.t_acc

        # # 6. Create Boolean masks for the four phases of the trajectory
        # mask_acc = t <= self.t_acc
        # mask_cruise = (t > self.t_acc) & (t <= (self.T - self.t_acc))
        # mask_dec = (t > (self.T - self.t_acc)) & (t < self.T)
        # mask_done = t >= self.T

        # # --- Phase 1: Accelerating ---
        # pos_acc = self.herk_start_pos + (0.5 * accel * t**2)
        # vel_acc = accel * t

        # # --- Phase 2: Cruising ---
        # pos_at_accel_end = self.herk_start_pos + (0.5 * accel * self.t_acc**2)
        # pos_cruise = pos_at_accel_end + (v_max * (t - self.t_acc))
        # vel_cruise = v_max  # Constant velocity

        # # --- Phase 3: Decelerating ---
        # pos_at_cruise_end = pos_at_accel_end + (v_max * (self.T - 2 * self.t_acc))
        # time_in_decel = t - (self.T - self.t_acc)
        # pos_dec = pos_at_cruise_end + (v_max * time_in_decel) - (0.5 * accel * time_in_decel**2)
        # vel_dec = v_max - (accel * time_in_decel)

        # # --- Phase 4: Done ---
        # pos_done = self.herk_goal_pos
        # vel_done = torch.zeros_like(pos_done)

        # # 7. Apply the piecewise POSITIONS based on the masks
        # self.herk_current_pos = torch.where(mask_acc, pos_acc, self.herk_current_pos)
        # self.herk_current_pos = torch.where(mask_cruise, pos_cruise, self.herk_current_pos)
        # self.herk_current_pos = torch.where(mask_dec, pos_dec, self.herk_current_pos)
        # self.herk_current_pos = torch.where(mask_done, pos_done, self.herk_current_pos)

        # # 8. Apply the piecewise VELOCITIES based on the masks
        # self.herk_current_vel = torch.where(mask_acc, vel_acc, self.herk_current_vel)
        # self.herk_current_vel = torch.where(mask_cruise, vel_cruise, self.herk_current_vel)
        # self.herk_current_vel = torch.where(mask_dec, vel_dec, self.herk_current_vel)
        # self.herk_current_vel = torch.where(mask_done, vel_done, self.herk_current_vel)

        # # 9. Fetch the actual joint states from the Genesis simulator
        # actual_pos = self.robot.get_dofs_position(self.motors_dof_idx)
        # actual_vel = self.robot.get_dofs_velocity(self.motors_dof_idx)

        # # 10. Calculate the True PD Error against the moving "ghost" target
        # pos_error = self.herk_current_pos - actual_pos
        # vel_error = self.herk_current_vel - actual_vel

        # # Feedforward Torque: Proactively push based on desired speed
        # tau_ff = self.herk_Kff * self.herk_current_vel

        # # 11. Calculate custom torque
        # tau = (self.herk_Kp * pos_error) + (self.herk_Kd * vel_error) + tau_ff
        # #print("Calculated torque:\n",tau)
        # # 12. Clip torque to hardware limits to prevent simulation explosions
        # tau = torch.clamp(tau, min=-self.max_torque, max=self.max_torque)
        # #print("Clipped torque:\n",tau)
        # # 13. Apply raw forces to Genesis
        # self.robot.control_dofs_force(tau, self.motors_dof_idx)

        # # --- Step the Physics Scene ---
        # self.scene.step()


#       ==========================================================
        # 4. HIGH-FREQUENCY CONTROL SUB-STEPPING LOOP (1000Hz)
        # ==========================================================
        for _ in range(self.control_substeps):
            
            # A. Advance time by ONE MILLISECOND (sim_dt), not the full RL dt
            self.herk_time_elapsed += self.sim_dt
            t = self.herk_time_elapsed

            # B. Calculate Trapezoidal Kinematics
            D = self.herk_goal_pos - self.herk_start_pos
            v_max = D / (self.T - self.t_acc)
            accel = v_max / self.t_acc

            # C. Create Boolean masks for the four phases
            mask_acc = t <= self.t_acc
            mask_cruise = (t > self.t_acc) & (t <= (self.T - self.t_acc))
            mask_dec = (t > (self.T - self.t_acc)) & (t < self.T)
            mask_done = t >= self.T

            # --- Phase Math ---
            pos_acc = self.herk_start_pos + (0.5 * accel * t**2)
            vel_acc = accel * t

            pos_at_accel_end = self.herk_start_pos + (0.5 * accel * self.t_acc**2)
            pos_cruise = pos_at_accel_end + (v_max * (t - self.t_acc))
            vel_cruise = v_max  

            pos_at_cruise_end = pos_at_accel_end + (v_max * (self.T - 2 * self.t_acc))
            time_in_decel = t - (self.T - self.t_acc)
            pos_dec = pos_at_cruise_end + (v_max * time_in_decel) - (0.5 * accel * time_in_decel**2)
            vel_dec = v_max - (accel * time_in_decel)

            pos_done = self.herk_goal_pos
            vel_done = torch.zeros_like(pos_done)

            # D. Apply piecewise POSITIONS and VELOCITIES based on masks
            self.herk_current_pos = torch.where(mask_acc, pos_acc, self.herk_current_pos)
            self.herk_current_pos = torch.where(mask_cruise, pos_cruise, self.herk_current_pos)
            self.herk_current_pos = torch.where(mask_dec, pos_dec, self.herk_current_pos)
            self.herk_current_pos = torch.where(mask_done, pos_done, self.herk_current_pos)

            self.herk_current_vel = torch.where(mask_acc, vel_acc, self.herk_current_vel)
            self.herk_current_vel = torch.where(mask_cruise, vel_cruise, self.herk_current_vel)
            self.herk_current_vel = torch.where(mask_dec, vel_dec, self.herk_current_vel)
            self.herk_current_vel = torch.where(mask_done, vel_done, self.herk_current_vel)

            # E. Fetch actual joint states
            actual_pos = self.robot.get_dofs_position(self.motors_dof_idx)
            actual_vel = self.robot.get_dofs_velocity(self.motors_dof_idx)

            # F. Calculate Error
            pos_error = self.herk_current_pos - actual_pos
            vel_error = self.herk_current_vel - actual_vel

            # G. Feedforward & Feedback Torque Calculation
            tau_ff = self.herk_Kff * self.herk_current_vel
            tau = (self.herk_Kp * pos_error) + (self.herk_Kd * vel_error) + tau_ff
            
            # Clip to hardware limits (Bring this back down to reality!)
            tau = torch.clamp(tau, min=-self.max_torque, max=self.max_torque)
            # print("Calculated torque:\n",tau)
            
            # H. Apply raw forces
            self.robot.control_dofs_force(tau, self.motors_dof_idx)

            # I. Step the Physics Scene (advances simulation by 0.001s)
            self.scene.step()

        #############################################################################
        # update buffers
        self.episode_length_buf += 1
        self.base_pos[:] = self.robot.get_pos()
        self.base_quat[:] = self.robot.get_quat()
        self.base_euler = quat_to_xyz(
            transform_quat_by_quat(torch.ones_like(self.base_quat) * self.inv_base_init_quat, self.base_quat),
        )
        inv_base_quat = inv_quat(self.base_quat)
        self.base_lin_vel[:] = transform_by_quat(self.robot.get_vel(), inv_base_quat)
        self.base_ang_vel[:] = transform_by_quat(self.robot.get_ang(), inv_base_quat)
        self.projected_gravity = transform_by_quat(self.global_gravity, inv_base_quat)
        self.dof_pos[:] = self.robot.get_dofs_position(self.motors_dof_idx)
        self.dof_vel[:] = self.robot.get_dofs_velocity(self.motors_dof_idx)

        # resample commands
        envs_idx = (
            (self.episode_length_buf % int(self.env_cfg["resampling_time_s"] / self.dt) == 0)
            .nonzero(as_tuple=False)
            .flatten()
        )
        self._resample_commands(envs_idx)

        # check termination and reset
        self.reset_buf = self.episode_length_buf > self.max_episode_length
        self.reset_buf |= torch.abs(self.base_euler[:, 1]) > self.env_cfg["termination_if_pitch_greater_than"]
        self.reset_buf |= torch.abs(self.base_euler[:, 0]) > self.env_cfg["termination_if_roll_greater_than"]

        # self-collision termination
        # this led to all sessions termination
        #self.reset_buf |= len(self.get_self_collision()) > 0

        time_out_idx = (self.episode_length_buf > self.max_episode_length).nonzero(as_tuple=False).flatten()
        self.extras["time_outs"] = torch.zeros_like(self.reset_buf, device=gs.device, dtype=gs.tc_float)
        self.extras["time_outs"][time_out_idx] = 1.0

        self.reset_idx(self.reset_buf.nonzero(as_tuple=False).flatten())

        # compute reward
        self.rew_buf[:] = 0.0
        for name, reward_func in self.reward_functions.items():
            rew = reward_func() * self.reward_scales[name]
            self.rew_buf += rew
            self.episode_sums[name] += rew

        # compute observations
        time_progress = (self.episode_length_buf / self.max_episode_length).unsqueeze(-1)
        self.obs_buf = torch.cat(
            [
                self.base_ang_vel * self.obs_scales["ang_vel"],  # 3
                # remove euler angles or projected gravity later
                self.projected_gravity,  # 3
                #self.base_euler * self.obs_scales["euler_angles"], # 3
                self.commands * self.commands_scale,  # 3
                (self.dof_pos - self.default_dof_pos) * self.obs_scales["dof_pos"],  # 12
                self.dof_vel * self.obs_scales["dof_vel"],  # 12
                self.actions,  # 12
                time_progress * self.obs_scales["time"], # 1
            ],
            axis=-1,
        )

        self.last_actions[:] = self.actions[:]
        self.last_dof_vel[:] = self.dof_vel[:]

        self.extras["observations"]["critic"] = self.obs_buf

        return self.obs_buf, self.rew_buf, self.reset_buf, self.extras

    def get_observations(self):
        self.extras["observations"]["critic"] = self.obs_buf
        return self.obs_buf, self.extras

    def get_privileged_observations(self):
        return None
    
    def get_self_collision(self):
        self_collision = [x  for x in self.robot.detect_collision() if x[0]!=0] # unique collisions between links
        return self_collision
    
    def get_joint_torques(self):
        dofs_idx = [self.robot.get_joint(name).dof_idx_local for name in self.env_cfg["joint_names"]]
        return self.robot.get_dofs_force(dofs_idx)
    
    def get_feet_pos(self):
        # try name-based lookup first (preferred)
        # try:
        r_idx = 11
        l_idx = 12
        links_pos = self.robot.get_links_pos().cpu().numpy() # shape: (num_envs, num_links, 3)
        r_pos = links_pos[:, r_idx]
        l_pos = links_pos[:, l_idx]
        return r_pos, l_pos
    
    def get_feet_height(self):
        r_idx = 11
        l_idx = 12
        links_pos = self.robot.get_links_pos().cpu().numpy() # shape: (num_envs, num_links, 3)
        r_height = links_pos[:, r_idx,2]
        l_height = links_pos[:, l_idx,2]
        return r_height, l_height

    def reset_idx(self, envs_idx):
        if len(envs_idx) == 0:
            return

        # reset dofs
        self.dof_pos[envs_idx] = self.default_dof_pos
        self.dof_vel[envs_idx] = 0.0
        ### new addition by ChatGPT ###
        # Reset previous target to default (so velocity target starts at 0)
        #self.prev_target_dof_pos[envs_idx] = self.default_dof_pos
        # --- NEW: Reset Custom Herkulex Tensors ---
        # Snap the moving ghost targets back to the default standing pose
        self.herk_goal_pos[envs_idx] = self.default_dof_pos
        self.herk_start_pos[envs_idx] = self.default_dof_pos
        self.herk_current_pos[envs_idx] = self.default_dof_pos
        self.herk_current_vel[envs_idx] = 0.0
        
        # Fast-forward the timer so the trapezoid math holds the default pose 
        # instead of trying to accelerate from zero.
        self.herk_time_elapsed[envs_idx] = self.T
        ###############################
        self.robot.set_dofs_position(
            position=self.dof_pos[envs_idx],
            dofs_idx_local=self.motors_dof_idx,
            zero_velocity=True,
            envs_idx=envs_idx,
        )

        # reset base
        self.base_pos[envs_idx] = self.base_init_pos
        self.base_quat[envs_idx] = self.base_init_quat.reshape(1, -1)
        self.robot.set_pos(self.base_pos[envs_idx], zero_velocity=False, envs_idx=envs_idx)
        self.robot.set_quat(self.base_quat[envs_idx], zero_velocity=False, envs_idx=envs_idx)
        self.base_lin_vel[envs_idx] = 0
        self.base_ang_vel[envs_idx] = 0
        self.robot.zero_all_dofs_velocity(envs_idx)

        # reset buffers
        self.last_actions[envs_idx] = 0.0
        self.last_dof_vel[envs_idx] = 0.0
        self.episode_length_buf[envs_idx] = 0
        self.reset_buf[envs_idx] = True
        # Reset last_rewarded_leg for these envs
        self.last_rewarded_leg[envs_idx] = -1

        # fill extras
        self.extras["episode"] = {}
        for key in self.episode_sums.keys():
            self.extras["episode"]["rew_" + key] = (
                torch.mean(self.episode_sums[key][envs_idx]).item() / self.env_cfg["episode_length_s"]
            )
            self.episode_sums[key][envs_idx] = 0.0

        self._resample_commands(envs_idx)

    def reset(self):
        self.reset_buf[:] = True
        self.reset_idx(torch.arange(self.num_envs, device=gs.device))
        return self.obs_buf, None


    # ------------ reward functions----------------
    def _reward_tracking_lin_vel(self):
        # Tracking of linear velocity commands (xy axes)
        lin_vel_error = torch.sum(torch.square(self.commands[:, :2] - self.base_lin_vel[:, :2]), dim=1)
        return torch.exp(-lin_vel_error / self.reward_cfg["tracking_sigma"])

    def _reward_tracking_ang_vel(self):
        # Tracking of angular velocity commands (yaw)
        ang_vel_error = torch.square(self.commands[:, 2] - self.base_ang_vel[:, 2])
        return torch.exp(-ang_vel_error / self.reward_cfg["tracking_sigma"])

    def _reward_lin_vel_z(self):
        # Penalize z axis base linear velocity
        return torch.square(self.base_lin_vel[:, 2])

    def _reward_action_rate(self):
        # Penalize changes in actions
        return torch.sum(torch.square(self.last_actions - self.actions), dim=1)

    def _reward_similar_to_default(self):
        # Penalize joint poses far away from default pose (with per-joint weights)
        return torch.sum(self.similar_to_default_weights * torch.abs(self.dof_pos - self.default_dof_pos), dim=1)

    # def _reward_base_height(self):
    #     # Penalize base height away from target
    #     return torch.square(self.base_pos[:, 2] - self.reward_cfg["base_height_target"])
    def _reward_base_height(self):
        # POSITIVE REWARD: +1.0 for standing at the target height, decays as it falls
        height_error = torch.square(self.base_pos[:, 2] - self.reward_cfg["base_height_target"])
        return torch.exp(-height_error / 0.01)
    
    def _reward_collision(self):
        # Return a per-environment collision penalty tensor.
        # `get_self_collision()` returns a list of collisions (may be empty).
        num_collisions = len(self.get_self_collision())
        if num_collisions == 0:
            return torch.zeros((self.num_envs,), device=gs.device, dtype=gs.tc_float)
        return torch.full((self.num_envs,), float(num_collisions), device=gs.device, dtype=gs.tc_float)
    
    def _reward_feet_height_alternate(self):
        r_height, l_height = self.get_feet_height()

        # Convert to torch tensors on the right device/dtype if needed
        if not torch.is_tensor(r_height):
            r_height = torch.tensor(r_height, device=gs.device, dtype=gs.tc_float)
        else:
            r_height = r_height.to(device=gs.device, dtype=gs.tc_float)

        if not torch.is_tensor(l_height):
            l_height = torch.tensor(l_height, device=gs.device, dtype=gs.tc_float)
        else:
            l_height = l_height.to(device=gs.device, dtype=gs.tc_float)

        reward = torch.zeros(self.num_envs, device=gs.device, dtype=gs.tc_float)
        threshold = float(self.reward_cfg["feet_height_target_difference"])

        # signed and absolute difference
        diff_signed = r_height - l_height
        diff_abs = torch.abs(diff_signed)

        # masks for which leg is higher and also not the last rewarded leg
        mask_right = (diff_signed > 0.0) & (self.last_rewarded_leg != 0)
        mask_left = (diff_signed < 0.0) & (self.last_rewarded_leg != 1)

        # compute ramped reward (normalized to [0,1] by threshold)
        # values above threshold are clipped to 1.0
        ramp = torch.clamp(diff_abs / threshold, min=0.0, max=1.0)
        exp = torch.exp(-diff_abs / threshold)

        # assign ramped rewards only for the eligible envs
        reward[mask_right] = ramp[mask_right]
        reward[mask_left] = ramp[mask_left]
        # reward[mask_right] = exp[mask_right]
        # reward[mask_left] = exp[mask_left]

        # set 0 for right-rewarded, 1 for left-rewarded
        self.last_rewarded_leg[mask_right] = 0
        self.last_rewarded_leg[mask_left] = 1

        return reward
