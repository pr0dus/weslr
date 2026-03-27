# robotics_knowledge.py - Robotics foundation for Weslr
"""
Robotics concepts that Weslr should understand to model embodied systems,
movement, sensing, and interaction with physical environments.
"""
from __future__ import annotations

# ============================================================================
# ROBOTICS FOUNDATION
# ============================================================================

ROBOTICS_FOUNDATIONS = {
    # Robot Components
    "robot_components": {
        "sensors": {
            "cameras": "vision, visual odometry",
            "lidar": "laser distance measurement",
            "sonar": "sound wave distance",
            "imu": "accelerometer, gyroscope, compass",
            "touch": "contact, pressure, force",
        },
        "actuators": {
            "motors": "DC, stepper, servo",
            "hydraulics": "fluid pressure",
            "pneumatics": "air pressure",
            "piezo": "piezoelectric actuators",
        },
        "controllers": {
            "microcontroller": "Arduino, Raspberry Pi",
            "processor": "CPU/GPU for higher-level control",
            "firmware": "embedded software",
        },
    },
    
    # Robot Types
    "robot_types": {
        "industrial": {
            "description": "Fixed-base, factory automation",
            "examples": ["arm robots", "conveyor systems"],
            "characteristics": ["precision", "repeatability", "high load"],
        },
        "mobile": {
            "description": "Mobile platforms",
            "types": {
                "wheeled": [" differential", "omni", "mecanum"],
                "tracked": ["tank treads", "continuous track"],
                "legged": ["bipedal", "quadrupedal", "hexapod"],
                "hovering": ["drones", "quadcopters"],
            },
            "characteristics": ["navigation", "obstacle avoidance"],
        },
        "humanoid": {
            "description": "Human-shaped robots",
            "examples": ["Boston Dynamics Atlas", "Honda ASIMO"],
            "characteristics": ["balance", "dexterity", "social interaction"],
        },
        "collaborative": {
            "description": "Work alongside humans safely",
            "characteristics": ["force limiting", "collision detection", "intuitive control"],
        },
    },
    
    # Kinematics
    "kinematics": {
        "forward": {
            "description": "Joint angles → end effector position",
            "usage": "Control, visualization",
        },
        "inverse": {
            "description": "End effector position → joint angles",
            "usage": "Path planning, control",
        },
        "types": {
            "prismatic": "linear motion (sliders)",
            "revolute": "rotary motion (joints)",
            "spherical": "3D rotation",
        },
    },
    
    # Dynamics
    "dynamics": {
        "newton_euler": "Force/torque analysis",
        "lagrangian": "Energy-based approach",
        "jacobian": "Velocity relationship",
    },
    
    # Path Planning
    "path_planning": {
        "methods": {
            "grid_based": ["A*", "Dijkstra"],
            "sample_based": ["RRT", "PRM"],
            "optimization": ["trajectory optimization", "nonlinear programming"],
        },
        "constraints": {
            "collision_free": "no obstacles",
            "smooth": "continuous path",
            "dynamic_feasible": "robot can execute",
        },
    },
    
    # Control
    "control": {
        "types": {
            "open_loop": "precomputed commands",
            "closed_loop": "feedback control",
        },
        "strategies": {
            "pid": "proportional-integral-derivative",
            "mpc": "model predictive control",
            "adaptive": "learn from experience",
        },
        "stability": "Lyapunov stability, BIBO stability",
    },
    
    # Localization
    "localization": {
        "methods": {
            "odometry": "wheel encoder integration",
            "filtering": ["EKF", "Particle Filter", "ICP"],
            "slam": "Simultaneous Localization and Mapping",
        },
        "uncertainty": "Bayesian estimation, covariance",
    },
    
    # Mapping
    "mapping": {
        "types": {
            "occupancy_grid": "cell-based probability",
            "point_cloud": "3D laser scan data",
            "topological": "nodes and edges",
        },
        "challenges": ["drift", "loop closure", "data association"],
    },
    
    # Sensing
    "sensing": {
        "modalities": {
            "visual": "cameras, depth sensors",
            "inertial": "IMU for orientation",
            "tactile": "skin sensors",
            "auditory": "microphones",
        },
        "fusion": "multi-sensor data combination",
    },
    
    # AI in Robotics
    "robotic_ai": {
        "perception": {
            "vision": "object detection, segmentation",
            "language": "command understanding",
            "fusion": "combine multiple sensors",
        },
        "planning": {
            "reactive": "speed-distance-avoid",
            "deliberative": "goal-directed search",
            "hybrid": "both reactive and deliberative",
        },
        "learning": {
            "reinforcement": "learn from rewards",
            "imitation": "learn from demonstrations",
            "transfer": "learn from simulation to reality",
        },
    },
}

# ============================================================================
# ROBOTICS TEACHING STRATEGY
# ============================================================================

ROBOTICS_TEACHING_STRATEGY = {
    "approach": "hardware_then_abstraction",
    "methods": [
        "sensing_first",       # How does robot perceive world?
        "actuation",           # How does robot move?
        "control_loop",        # Perception → Decision → Action
        "integration",         # Combine subsystems
    ],
}

# ============================================================================
# ROBOTICS SELF-TEST QUESTIONS
# ============================================================================

ROBOTICS_SELF_TEST_QUESTIONS = [
    {
        "question": "How does a robot know its position?",
        "mechanism": "localization",
        "robotics_concept": "sensor fusion and state estimation",
    },
    {
        "question": "How does a robot avoid obstacles?",
        "mechanism": "collision_avoidance",
        "robotics_concept": "perception and reactive control",
    },
    {
        "question": "How does a robot move precisely?",
        "mechanism": "control_system",
        "robotics_concept": "kinematics and dynamics control",
    },
]

# ============================================================================
# ROBOTICS KNOWLEDGE ACCESS
# ============================================================================

def get_robotics_concept(concept_name: str) -> dict:
    """Get a specific robotics concept."""
    return ROBOTICS_FOUNDATIONS.get(concept_name, {})


def get_all_robotics_concepts() -> list:
    """Get all available robotics concepts."""
    return list(ROBOTICS_FOUNDATIONS.keys())


def robot_type_classification(robot_description: str) -> dict:
    """
    Classify robot type based on description.
    """
    desc_lower = robot_description.lower()
    
    classification = {
        "type": "unknown",
        "characteristics": [],
        "confidence": 0.0,
    }
    
    # Check for mobile base
    if any(word in desc_lower for word in ["wheeled", "mobile", "car", "tank"]):
        classification["type"] = "mobile"
        classification["characteristics"].append("mobile platform")
    
    # Check for arm
    if any(word in desc_lower for word in ["arm", "manipulator", "robotic arm"]):
        classification["type"] = "industrial"
        classification["characteristics"].append("robotic arm")
    
    # Check for humanoid
    if any(word in desc_lower for word in ["humanoid", "human-like", "two-legged", "biped"]):
        classification["type"] = "humanoid"
        classification["characteristics"].append("humanoid form")
    
    # Check for drone
    if any(word in desc_lower for word in ["drone", "quadcopter", "uav", "airborne"]):
        classification["type"] = "mobile"
        classification["characteristics"].append("flying platform")
    
    # Add default confidence
    classification["confidence"] = 0.7 if classification["type"] != "unknown" else 0.0
    
    return classification


def sensor_fusion_plan(sensors: list) -> dict:
    """
    Plan sensor fusion for a robot.
    """
    fusion_plan = {
        "sensors": sensors,
        "fusion_strategy": "complementary_filter",
        "outputs": [],
    }
    
    for sensor in sensors:
        sensor_lower = sensor.lower()
        
        if "camera" in sensor_lower:
            fusion_plan["outputs"].append("visual odometry")
            fusion_plan["outputs"].append("object detection")
        elif "lidar" in sensor_lower:
            fusion_plan["outputs"].append("distance map")
            fusion_plan["outputs"].append("obstacle detection")
        elif "imu" in sensor_lower:
            fusion_plan["outputs"].append("orientation")
            fusion_plan["outputs"].append("acceleration")
        elif "sonar" in sensor_lower:
            fusion_plan["outputs"].append("proximity")
            fusion_plan["outputs"].append("wall detection")
        elif "encoder" in sensor_lower or "wheel" in sensor_lower:
            fusion_plan["outputs"].append("odometry")
    
    return fusion_plan


def control_system_design(control_type: str, robot_type: str) -> dict:
    """
    Design a control system based on requirements.
    """
    control_design = {
        "control_type": control_type,
        "robot_type": robot_type,
        "strategy": "",
        "components": [],
    }
    
    # Strategy selection
    if control_type == "closed_loop":
        control_design["strategy"] = "feedback control with error correction"
    elif control_type == "open_loop":
        control_design["strategy"] = "precomputed trajectory execution"
    else:
        control_design["strategy"] = "hybrid approach"
    
    # Components based on robot type
    if robot_type in ["mobile", "wheeled"]:
        control_design["components"].extend(["speed controller", "steering controller", "odometry integration"])
    elif robot_type in ["humanoid"]:
        control_design["components"].extend(["balance controller", "gait generator", "fall recovery"])
    elif robot_type in ["industrial", "arm"]:
        control_design["components"].extend(["joint torque control", "end-effector position", "collision detection"])
    
    return control_design


def kinematics_chain(joint_types: list, link_lengths: list) -> dict:
    """
    Analyze a kinematics chain.
    """
    chain = {
        "joints": joint_types,
        "links": link_lengths,
        "chain_type": "serial",
        "dof": len(joint_types),
    }
    
    # Determine if redundant
    if len(joint_types) > 6:
        chain["redundant"] = True
        chain["redundancy"] = len(joint_types) - 6
    else:
        chain["redundant"] = False
    
    return chain


def robotics_integration_plan(modules: list) -> dict:
    """
    Plan integration of robotics modules.
    """
    plan = {
        "modules": modules,
        "integration_order": [],
        "interface_standards": ["ROS topics", "TF transforms", "action servers"],
        "challenges": [],
    }
    
    # Determine order based on dependencies
    order_map = {
        "sensors": ["localization", "mapping"],
        "localization": ["navigation"],
        "mapping": ["navigation"],
        "navigation": ["planning"],
        "planning": ["control"],
        "control": ["actuators"],
    }
    
    # Build integration order
    for module in modules:
        plan["integration_order"].append(module)
    
    return plan
