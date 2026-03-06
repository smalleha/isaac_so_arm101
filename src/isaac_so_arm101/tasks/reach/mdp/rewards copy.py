# Copyright (c) 2024-2025, Muammer Bay (LycheeAI), Louis Le Lay
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from isaaclab.assets import RigidObject
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer
from isaaclab.utils.math import combine_frame_transforms

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv

#是否抬起物体
def object_is_lifted(
    env: ManagerBasedRLEnv, minimal_height: float, object_cfg: SceneEntityCfg = SceneEntityCfg("object")
) -> torch.Tensor:
    """Reward the agent for lifting the object above the minimal height."""
    object: RigidObject = env.scene[object_cfg.name]
    return torch.where(object.data.root_pos_w[:, 2] > minimal_height, 1.0, 0.0)

#末端是否靠近物体
def object_ee_distance(
    env: ManagerBasedRLEnv,
    std: float,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    """Reward the agent for reaching the object using tanh-kernel."""
    # extract the used quantities (to enable type-hinting)
    #获取机械臂本体和机械臂末端
    object: RigidObject = env.scene[object_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    # Target object position: (num_envs, 3)
    cube_pos_w = object.data.root_pos_w
    # End-effector position: (num_envs, 3)
    ee_w = ee_frame.data.target_pos_w[..., 0, :]
    # Distance of the end-effector to the object: (num_envs,)
    object_ee_distance = torch.norm(cube_pos_w - ee_w, dim=1)

    return 1 - torch.tanh(object_ee_distance / std)

#是否把物体移动到目标
def object_goal_distance(
    env: ManagerBasedRLEnv,
    std: float,
    minimal_height: float,
    command_name: str,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """Reward the agent for tracking the goal pose using tanh-kernel."""
    # extract the used quantities (to enable type-hinting)
    robot: RigidObject = env.scene[robot_cfg.name]
    object: RigidObject = env.scene[object_cfg.name]
    command = env.command_manager.get_command(command_name)
    # compute the desired position in the world frame
    #获取目标点到base_link的位置
    des_pos_b = command[:, :3]
    #将目标位置从机器人基座坐标系转到世界坐标系
    #分别获取机器人的Position和Orientation
    des_pos_w, _ = combine_frame_transforms(robot.data.root_state_w[:, :3], robot.data.root_state_w[:, 3:7], des_pos_b)
    # distance of the end-effector to the object: (num_envs,)
    distance = torch.norm(des_pos_w - object.data.root_pos_w[:, :3], dim=1)
    # rewarded if the object is lifted above the threshold
    return (object.data.root_pos_w[:, 2] > minimal_height) * (1 - torch.tanh(distance / std))

# 计算各类惩罚项
def compute_penalties(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    penalty_weights: Optional[Dict[str, float]] = None
) -> torch.Tensor:
    """
    计算所有惩罚项并返回总惩罚值
    
    Args:
        env: 环境实例
        robot_cfg: 机器人配置
        penalty_weights: 惩罚权重配置，包含:
            - smooth_penalty_weight: 动作平滑惩罚权重
            - action_magnitude_weight: 动作幅值惩罚权重
            - contact_penalty_weight: 接触惩罚权重
            - joint_penalty_weight: 关节角度惩罚权重
    
    Returns:
        总惩罚值 (num_envs,)
    """
    # 设置默认惩罚权重
    default_weights = {
        "smooth_penalty_weight": 0.1,
        "action_magnitude_weight": 0.05,
        "contact_penalty_weight": 1.0,
        "joint_penalty_weight": 0.5,
    }
    weights = penalty_weights or default_weights
    
    # 1. 动作相关惩罚
    # 获取当前动作和上一步动作
    current_action = env.action  # (num_envs, num_actions)
    prev_action = getattr(env, 'prev_action', torch.zeros_like(current_action))
    
    # 动作变化惩罚 (平滑惩罚)
    action_diff = current_action - prev_action
    smooth_penalty = weights["smooth_penalty_weight"] * torch.norm(action_diff, dim=1)
    
    # 动作幅值惩罚
    action_magnitude_penalty = weights["action_magnitude_weight"] * torch.norm(current_action, dim=1)
    
    # 保存当前动作作为下一步的prev_action
    env.prev_action = current_action.clone()
    
    # 2. 接触惩罚
    # ncon是每个环境的接触数量 (num_envs,)
    contact_penalty = weights["contact_penalty_weight"] * env.scene.data.ncon.float()
    
    # 3. 关节角度限制惩罚
    robot: RigidObject = env.scene[robot_cfg.name]
    # 获取前6个关节的角度 (num_envs, 6)
    joint_angles = robot.data.joint_pos[:, :6]
    # 获取前6个关节的角度限制 (6, 2) -> (min, max)
    joint_limits = robot.data.joint_limits[:6]
    min_angles = joint_limits[:, 0].unsqueeze(0)  # (1, 6)
    max_angles = joint_limits[:, 1].unsqueeze(0)  # (1, 6)
    
    # 计算低于最小值的惩罚
    below_min = torch.clamp(min_angles - joint_angles, min=0.0)
    # 计算高于最大值的惩罚
    above_max = torch.clamp(joint_angles - max_angles, min=0.0)
    # 总关节惩罚 (num_envs,)
    joint_penalty = weights["joint_penalty_weight"] * (below_min + above_max).sum(dim=1)
    
    # 计算总惩罚
    total_penalty = smooth_penalty + action_magnitude_penalty + contact_penalty + joint_penalty
    
    return total_penalty


#靠近 + 抬起组合奖励
def object_ee_distance_and_lifted(
    env: ManagerBasedRLEnv,
    std: float,
    minimal_height: float,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    """Combined reward for reaching the object AND lifting it."""
    # Get reaching reward
    reach_reward = object_ee_distance(env, std, object_cfg, ee_frame_cfg)
    # Get lifting reward
    lift_reward = object_is_lifted(env, minimal_height, object_cfg)
    reward = reach_reward * lift_reward
    reward = torch.clamp(reward, min=-1.0, max=1.0)
    # Combine rewards multiplicatively
    print("reach_reward: ",reach_reward)
    print("lift_reward: ",lift_reward)
    return reach_reward * lift_reward
