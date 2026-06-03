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
from isaac_so_arm101.robots import DUAL_NERO_CFG # noqa: F401   
from isaac_so_arm101.tasks.reach.dual_nero_reach_env_cfg import Dual_NeroReachEnvCfg
from isaaclab.assets.articulation import ArticulationCfg

##  
# Scene definition
##


@configclass
class Dual_Nero_ReachEnvCfg(Dual_NeroReachEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()

        # switch robot to OpenArm
        self.scene.robot = DUAL_NERO_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot",)

        # override rewards
        self.rewards.left_end_effector_position_tracking.params["asset_cfg"].body_names = ["left_gripper_base"]
        self.rewards.left_end_effector_position_tracking_fine_grained.params["asset_cfg"].body_names = [
            "left_gripper_base"
        ]
        self.rewards.left_end_effector_orientation_tracking.params["asset_cfg"].body_names = ["left_gripper_base"]

        self.rewards.right_end_effector_position_tracking.params["asset_cfg"].body_names = ["right_gripper_base"]
        self.rewards.right_end_effector_position_tracking_fine_grained.params["asset_cfg"].body_names = [
            "right_gripper_base"
        ]
        self.rewards.right_end_effector_orientation_tracking.params["asset_cfg"].body_names = ["right_gripper_base"]

        # override actions
        self.actions.left_arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=[
                "left_joint.*",
            ],
            scale=0.5,
            use_default_offset=True,
        )

        self.actions.right_arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=[
                "right_joint.*",
            ],
            scale=0.5,
            use_default_offset=True,
        )

        # override command generator body
        # end-effector is along z-direction
        self.commands.left_ee_pose.body_name = "left_gripper_base"
        self.commands.right_ee_pose.body_name = "right_gripper_base"



@configclass    
class Dual_Nero_ReachEnvCfg_PLAY(Dual_Nero_ReachEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()
        # make a smaller scene for play
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        # disable randomization for play
        self.observations.policy.enable_corruption = False

