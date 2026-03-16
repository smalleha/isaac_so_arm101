from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

TEMPLATE_ASSETS_DATA_DIR = Path(__file__).resolve().parent

##
# Configuration
##

NERO_CFG = ArticulationCfg(
    spawn=sim_utils.UrdfFileCfg(
        fix_base=True,
        replace_cylinders_with_capsules=True,
        asset_path="/home/agilex/Isaac/IsaacLab/source/isaaclab_assets/isaaclab_assets/robots/nero_description/urdf/nero_description_stand_v2.urdf",
        activate_contact_sensors=False, # set as false while waiting for capsule implementation
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=0,
        ),
        joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
            gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=0, damping=0)
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        rot=(0.0, 0.0, 0.0, 0.0),
        joint_pos={
            "joint1": 0.0,
            "joint2": 0.0,
            "joint3": 0.0,
            "joint4": 0.0,
            "joint5": 0.0,
            "joint6": 0.0,
            "joint7": 0.0,
        },
        # Set initial joint velocities to zero
        joint_vel={".*": 0.0},
    ),
    actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["joint.*"],
                effort_limit=200.0, # 稍微限制出力，防止瞬间冲击
                velocity_limit=1.5,
                
                # 刚度 (Stiffness)：针对轻型臂 Nero 优化，不再追求极致硬度
                stiffness={
                    "joint1": 200.0, 
                    "joint2": 200.0,
                    "joint3": 150.0,
                    "joint4": 150.0,
                    "joint5": 80.0,
                    "joint6": 80.0,
                    "joint7": 80.0,
                    # "end_effector_joint": 100,

                },
                
                # 阻尼 (Damping)：采用临界阻尼思路，比例设在 10% 左右
                damping={
                    "joint1": 20.0,
                    "joint2": 20.0,
                    "joint3": 15.0,
                    "joint4": 15.0,
                    "joint5": 8.0,
                    "joint6": 8.0,
                    "joint7": 8.0,
                    # "end_effector_joint": 10.0,
                },
            ),
        },
    soft_joint_pos_limit_factor=1.0,
)
"""Configuration of SO-ARM robot arm."""

