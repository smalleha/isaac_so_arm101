from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

TEMPLATE_ASSETS_DATA_DIR = Path(__file__).resolve().parent

##
# Configuration
##

PIPER_CFG = ArticulationCfg(
    spawn=sim_utils.UrdfFileCfg(
        fix_base=True,
        replace_cylinders_with_capsules=True,
        asset_path=f"{TEMPLATE_ASSETS_DATA_DIR}/urdf/piper_description_v100_realsense_camera_v2_dark.urdf",
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
        rot=(1.0, 0.0, 0.0, 0.0),
        joint_pos={
            "joint1": 0.0,
            "joint2": 0.0,
            "joint3": 0.0,
            "joint4": 0.0,
            "joint5": 0.0,
            "joint6": 0.0,
            "piper_finger_joint7": 0.05,
            "piper_finger_joint8": -0.05
        },
        # Set initial joint velocities to zero
        joint_vel={".*": 0.0},
    ),
    actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["joint.*"],
                effort_limit=25.0, # 稍微限制出力，防止瞬间冲击
                velocity_limit=1.5,
                
                # 刚度 (Stiffness)：针对轻型臂 Piper 优化，不再追求极致硬度
                stiffness={
                    "joint1": 200.0, 
                    "joint2": 170.0,
                    "joint3": 120.0,
                    "joint4": 80.0,
                    "joint5": 50.0,
                    "joint6": 20.0,
                },
                
                # 阻尼 (Damping)：采用临界阻尼思路，比例设在 10% 左右
                damping={
                    "joint1": 100.0,
                    "joint2": 60.0,
                    "joint3": 70.0,
                    "joint4": 24.0,
                    "joint5": 20.0,
                    "joint6": 10.0,
                },
            ),
        "gripper": ImplicitActuatorCfg(
            joint_names_expr=["piper_finger_joint7","piper_finger_joint8"],
            effort_limit_sim=22,  # Increased from 1.9 to 2.5 for stronger grip
            velocity_limit_sim=1.5,
            stiffness=800.0,  # Increased from 25.0 to 60.0 for more reliable closing
            damping=20.0,  # Increased from 10.0 to 20.0 for stability
        ),

        },


    soft_joint_pos_limit_factor=0.9,
)