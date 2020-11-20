from flow.networks import Network
import numpy as np
from flow.core.params import VehicleParams, NetParams, InitialConfig, SumoParams, EnvParams
from flow.controllers import ContinuousRouter, IDMController, RLController
from flow.envs.ring.accel import AccelEnv, ADDITIONAL_ENV_PARAMS, LaneChangeAccelEnv
from flow.core.experiment import Experiment
from flow.controllers.base_lane_changing_controller import BaseLaneChangeController

ADDITIONAL_NET_PARAMS = {
    "radius": 40,
    "num_lanes": 1,
    "speed_limit": 30,
}

class CustomRingNetwork(Network):
    def specify_nodes(self, net_params):
        radius = net_params.additional_params["radius"]
        
        nodes = [{"id": "bottom", "x": 0, "y": -radius},
                 {"id": "top", "x": 0, "y": radius},
                 {"id": "left", "x": -radius, "y": 0},
                 {"id": "right", "x": radius, "y": 0}]
        return nodes
    
    def specify_edges(self, net_params):
        radius = net_params.additional_params["radius"]
        num_lanes = net_params.additional_params["num_lanes"]
        speed_limit = net_params.additional_params["speed_limit"]
        edge_length = radius * np.pi / 2

        edges = [
            {
                "id": "edge0",
                "numLanes": num_lanes,
                "speed": speed_limit,
                "from": "bottom",
                "to": "right",
                "length": edge_length,
                "shape": [(radius * np.sin(t), radius * np.cos(t)) for t in np.linspace(-np.pi / 2, 0, 40)],
                "priority": 2
            },
            {
                "id": "edge1",
                "numLanes": num_lanes + 2,
                "speed": speed_limit,
                "from": "right",
                "to": "top",
                "length": edge_length,
                "shape": [(radius * np.sin(t), radius * np.cos(t)) for t in np.linspace(0, np.pi / 2, 40)],
                "priority": 1
            },
            {
                "id": "edge2",
                "numLanes": num_lanes + 1,
                "speed": speed_limit,
                "from": "top",
                "to": "left",
                "length": edge_length,
                "shape": [(radius * np.sin(t), radius * np.cos(t)) for t in np.linspace(np.pi / 2, np.pi, 40)],
                "priority": 2
            },
            {
                "id": "edge3",
                "numLanes": num_lanes,
                "speed": speed_limit,
                "from": "left",
                "to": "bottom",
                "length": edge_length,
                "shape": [(radius * np.sin(t), radius * np.cos(t)) for t in np.linspace(np.pi, 3 * np.pi / 2, 40)],
                "priority": 3
            }
        ]
        return edges

    def specify_routes(self, net_params):
        routes = {"edge0": [(["edge0", "edge1", "edge2", "edge3"], 1)],
               "edge1": [(["edge1", "edge2", "edge3", "edge0"], 1)],
               "edge2": [(["edge2", "edge3", "edge0", "edge1"], 1)],
               "edge3": [(["edge3", "edge0", "edge1", "edge2"], 1)],
               "human_0": ["edge0", "edge1", "edge2", "edge3"]}
        return routes

    def specify_edge_starts(self):
        radius = self.net_params.additional_params["radius"]
        edge_starts = [("edge0", 0),
                        ("edge1", radius * np.pi / 2),
                        ("edge2", radius * np.pi),
                        ("edge3", radius * np.pi * 3 / 2)]
        return edge_starts

class CustomLaneChangeController(BaseLaneChangeController):
    def __init__(self, veh_id, time_between, lane_change_params=None):
        self.time_between = time_between
        self.last_change = 0
        super().__init__(veh_id, lane_change_params)

    def get_adjacent_lanes(self, cur_lane, num_lanes):

        if num_lanes == 2:
            if cur_lane == 0:
                return [1]
            else:
                return [0]
        if cur_lane == 0:
            return [1]
        if cur_lane == num_lanes - 1:
            return [-1]
        return [-1, 1]


    def get_lane_change_action(self, env):
        if self.last_change + self.time_between > env.step_counter:
            return 0
        cur_location = env.k.vehicle.get_position(self.veh_id)
        cur_lane = env.k.vehicle.get_lane(self.veh_id)
        cur_edge = env.k.vehicle.get_edge(self.veh_id)
        if cur_edge[0] != 'e':
            return 0

        num_lanes = env.k.network.num_lanes(cur_edge)
        if num_lanes == 0:
            return 0

        adjacent_lanes = self.get_adjacent_lanes(cur_lane, num_lanes)
        # for id in env.k.vehicle.get_ids():
            # if id != self.veh_id and :
        self.last_change = env.step_counter
        return np.random.choice(adjacent_lanes, size = 1)[0]


vehicles = VehicleParams()
vehicles.add(veh_id = "human", acceleration_controller = (IDMController, {}),
        routing_controller = (ContinuousRouter, {}), num_vehicles = 22, 
        lane_change_controller = (CustomLaneChangeController, {"time_between": 25}))
sim_params = SumoParams(sim_step = 0.1, render = True)
initial_config = InitialConfig(bunching = 40)

env_params = EnvParams(additional_params = ADDITIONAL_ENV_PARAMS)
net_params = NetParams(additional_params = ADDITIONAL_NET_PARAMS)

flow_params = dict(
    exp_tag = "custom_network",
    env_name = AccelEnv,
    network = CustomRingNetwork,
    simulator = 'traci',
    sim = sim_params,
    net = net_params,
    env = env_params,
    veh = vehicles,
    initial = initial_config,
)

flow_params['env'].horizon = 1500
exp = Experiment(flow_params = flow_params)
_ = exp.run(1)