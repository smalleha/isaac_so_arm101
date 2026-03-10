# Copyright (c) 2024-2025, Muammer Bay (LycheeAI), Louis Le Lay
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause


# import mdp
import math

import isaaclab_tasks.manager_based.manipulation.reach.mdp as mdp
from isaaclab.utils import configclass
from isaac_so_arm101.robots import NERO_CFG # noqa: F401
from isaac_so_arm101.tasks.reach.nero_reach_env_cfg import NeroReachEnvCfg

##
# Scene definition
##


@configclass
class Nero_ReachEnvCfg(NeroReachEnvCfg):
    def __post_init__(self):
        # post init of parent   
        super().__post_init__()

        # switch robot to franka
        self.scene.robot = NERO_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        # override rewards
        self.rewards.end_effector_position_tracking.params["asset_cfg"].body_names = ["world"]
        self.rewards.end_effector_position_tracking_fine_grained.params["asset_cfg"].body_names = ["world"]
        self.rewards.end_effector_orientation_tracking.params["asset_cfg"].body_names = ["world"]
        # self.rewards.action_rate
        # TODO: reorient command target

        # override actions
        self.actions.arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["joint1", "joint2", "joint3", "joint4", "joint5","joint6","joint7"],
            scale=0.5,
            use_default_offset=True,
        )
        # override command generator body
        # end-effector is along z-direction
        self.commands.ee_pose.body_name = "world"
        self.commands.ee_pose.ranges.pitch = (math.pi, math.pi)


@configclass
class Nero_ReachEnvCfg_PLAY(NeroReachEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()
        # make a smaller scene for play
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        # disable randomization for play
        self.observations.policy.enable_corruption = False

