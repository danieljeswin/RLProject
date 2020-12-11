

from flow.core.params import SumoParams, EnvParams, InitialConfig, NetParams, \
    InFlows, SumoCarFollowingParams, TrafficLightParams
from flow.core.params import VehicleParams
from flow.controllers import SimCarFollowingController, GridRouter, RLController , IDMController
# from flow.envs import TrafficLightGridPOEnv, TrafficLightGridEnv
# from flow.networks import TrafficLightGridNetwork

from environment import TrafficLightGridPOEnv
from network import TrafficLightGridNetwork




# time horizon of a single rollout
HORIZON = 800
# number of rollouts per training iteration
N_ROLLOUTS = 30
# number of parallel workers
N_CPUS = 10
# set to True if you would like to run the experiment with inflows of vehicles
# from the edges, and False otherwise
USE_INFLOWS = True


def gen_edges(col_num, row_num):
    """Generate the names of the outer edges in the traffic light grid network.
    Parameters
    ----------
    col_num : int
        number of columns in the traffic light grid
    row_num : int
        number of rows in the traffic light grid
    Returns
    -------
    list of str
        names of all the outer edges
    """
    edges = []
    for i in range(col_num):
        edges += ['left' + str(row_num) + '_' + str(i)]
        edges += ['right' + '0' + '_' + str(i)]

    # build the left and then the right edges
    for i in range(row_num):
        edges += ['bot' + str(i) + '_' + '0']
        edges += ['top' + str(i) + '_' + str(col_num)]

    return edges


def get_inflow_params(col_num, row_num, additional_net_params):
    """Define the network and initial params in the presence of inflows.
    Parameters
    ----------
    col_num : int
        number of columns in the traffic light grid
    row_num : int
        number of rows in the traffic light grid
    additional_net_params : dict
        network-specific parameters that are unique to the traffic light grid
    Returns
    -------
    flow.core.params.InitialConfig
        parameters specifying the initial configuration of vehicles in the
        network
    flow.core.params.NetParams
        network-specific parameters used to generate the network
    """
    initial = InitialConfig(
        spacing='custom', lanes_distribution=float('inf'), shuffle=True)

    inflow = InFlows()
    outer_edges = gen_edges(col_num, row_num)
    for i in range(len(outer_edges)):

        # inflow.add(
        #     veh_type='idm',
        #     edge=outer_edges[i],
        #     probability=0.1,
        #     depart_lane='free',
        #     depart_speed=10)

        inflow.add(
            veh_type='idh',
            edge=outer_edges[i],
            vehs_per_hour=3600*2,
            depart_lane='free',
            depart_speed=10,
            color='grey')

    net = NetParams(
        inflows=inflow,
        additional_params=additional_net_params)

    return initial, net


def get_non_flow_params(enter_speed, add_net_params):
    """Define the network and initial params in the absence of inflows.
    Note that when a vehicle leaves a network in this case, it is immediately
    returns to the start of the row/column it was traversing, and in the same
    direction as it was before.
    Parameters
    ----------
    enter_speed : float
        initial speed of vehicles as they enter the network.
    add_net_params: dict
        additional network-specific parameters (unique to the traffic light grid)
    Returns
    -------
    flow.core.params.InitialConfig
        parameters specifying the initial configuration of vehicles in the
        network
    flow.core.params.NetParams
        network-specific parameters used to generate the network
    """
    additional_init_params = {'enter_speed': enter_speed}
    initial = InitialConfig(
        spacing='custom', additional_params=additional_init_params)
    net = NetParams(additional_params=add_net_params)

    return initial, net


V_ENTER = 10
INNER_LENGTH = 300
LONG_LENGTH = 200
SHORT_LENGTH = 200
N_ROWS = 3
N_COLUMNS = 3
NUM_CARS_LEFT = 1
NUM_CARS_RIGHT = 1
NUM_CARS_TOP = 1
NUM_CARS_BOT = 1
tot_cars = ((NUM_CARS_LEFT + NUM_CARS_RIGHT) * N_COLUMNS \
           + (NUM_CARS_BOT + NUM_CARS_TOP) * N_ROWS)//10

grid_array = {
    "short_length": SHORT_LENGTH,
    "inner_length": INNER_LENGTH,
    "long_length": LONG_LENGTH,
    "row_num": N_ROWS,
    "col_num": N_COLUMNS,
    "cars_left": NUM_CARS_LEFT,
    "cars_right": NUM_CARS_RIGHT,
    "cars_top": NUM_CARS_TOP,
    "cars_bot": NUM_CARS_BOT
}

additional_env_params = {
        'target_velocity': 50,
        'switch_time': 60.0,
        'num_observed':20,
        'discrete': False,
        'tl_type': 'controlled'
    }

tl_logic = TrafficLightParams()

nodes = ["center0", "center1", "center2", "center3", "center4", "center5", "center6", "center7", "center8"]
# phases = [{"duration": "6", "state": "rrrr"}]

# phases = [{"duration":"31","state": ("ggg"+"ggg"+"ggg"+"ggg")}]

phases = [{"duration":"31","state": ("ggr"+"rrr"+"ggr"+"rrr")},
          {"duration":"31","state": ("rrr"+"ggr"+"rrr"+"ggr")},
          {"duration":"31","state": ("rrg"+"grr"+"rrg"+"grr")},
          {"duration":"31","state": ("grr"+"rrg"+"grr"+"rrg")},
          {"duration":"31","state": ("rrr"+"rrr"+"rrr"+"rrr")}]


for node_id in nodes:
    tl_logic.add(node_id, tls_type="static", programID="1", offset=None, phases=phases)


additional_net_params = {
    'speed_limit': 50,
    'grid_array': grid_array,
    'horizontal_lanes': 1,
    'vertical_lanes': 1,
    'traffic_lights': True
}

vehicles = VehicleParams()
vehicles.add(
    veh_id='idh',
    acceleration_controller=(IDMController, {}),
    car_following_params=SumoCarFollowingParams(
        min_gap=2.5,
        decel=10,  # avoid collisions at emergency stops
        max_speed=50,
        speed_mode="all_checks",
    ),
    routing_controller=(GridRouter, {}),
    num_vehicles=0,
    color="white")

# vehicles.add(
#     veh_id='idm',
#     acceleration_controller=(RLController, {}),
#     car_following_params=SumoCarFollowingParams(
#         min_gap=2.5,
#         decel=7.5,  # avoid collisions at emergency stops
#         max_speed=V_ENTER,
#         speed_mode="all_checks",
#     ),
#     routing_controller=(GridRouter, {}),
#     num_vehicles=tot_cars,
#     )

# collect the initialization and network-specific parameters based on the
# choice to use inflows or not
if USE_INFLOWS:
    initial_config, net_params = get_inflow_params(
        col_num=N_COLUMNS,
        row_num=N_ROWS,
        additional_net_params=additional_net_params)
else:
    initial_config, net_params = get_non_flow_params(
        enter_speed=V_ENTER,
        add_net_params=additional_net_params)



flow_params = dict(
    # name of the experiment
    exp_tag='traffic_light_grid',

    # name of the flow environment the experiment is running on
    env_name=TrafficLightGridPOEnv,

    # name of the network class the experiment is running on
    network=TrafficLightGridNetwork,

    # simulator that is used by the experiment
    simulator='traci',

    # sumo-related parameters (see flow.core.params.SumoParams)
    sim=SumoParams(
        sim_step=1,
        render=False,#True,
        restart_instance = True
    ),

    # environment related parameters (see flow.core.params.EnvParams)
    env=EnvParams(
        horizon=HORIZON,
        additional_params=additional_env_params,
    ),

    # network-related parameters (see flow.core.params.NetParams and the
    # network's documentation or ADDITIONAL_NET_PARAMS component). This is
    # filled in by the setup_exps method below.
    net=net_params,

    # vehicles to be placed in the network at the start of a rollout (see
    # flow.core.params.VehicleParams)
    veh=vehicles,

    # parameters specifying the positioning of vehicles upon initialization/
    # reset (see flow.core.params.InitialConfig). This is filled in by the
    # setup_exps method below.
    initial=initial_config,

    tls=tl_logic
)


# from flow.core.experiment import Experiment

# flow_params['env'].horizon = 3000
# exp = Experiment(flow_params)

# # run the sumo simulation
# _ = exp.run(1, convert_to_csv=False)




import json

import ray
try:
    from ray.rllib.agents.agent import get_agent_class
except ImportError:
    from ray.rllib.agents.registry import get_agent_class
from ray.tune import run_experiments
from ray.tune.registry import register_env

from flow.utils.registry import make_create_env
from flow.utils.rllib import FlowParamsEncoder

# The algorithm or model to train. This may refer to "
#      "the name of a built-on algorithm (e.g. RLLib's DQN "
#      "or PPO), or a user-defined trainable function or "
#      "class registered in the tune registry.")
alg_run = "PPO"

agent_cls = get_agent_class(alg_run)
config = agent_cls._default_config.copy()
config["num_workers"] = N_CPUS - 1  # number of parallel workers
config["train_batch_size"] = HORIZON * N_ROLLOUTS  # batch size
config["gamma"] = 0.999  # discount rate
config["model"].update({"fcnet_hiddens": [3000, 1000, 500]})  # size of hidden layers in network
config["use_gae"] = True  # using generalized advantage estimation
config["lambda"] = 0.97  
config["sgd_minibatch_size"] = min(16 * 1024, config["train_batch_size"])  # stochastic gradient descent
config["kl_target"] = 0.02  # target KL divergence
config["num_sgd_iter"] = 10  # number of SGD iterations
config["horizon"] = HORIZON  # rollout horizon

# save the flow params for replay
flow_json = json.dumps(flow_params, cls=FlowParamsEncoder, sort_keys=True,
                       indent=4)  # generating a string version of flow_params
config['env_config']['flow_params'] = flow_json  # adding the flow_params to config dict
config['env_config']['run'] = alg_run

# Call the utility function make_create_env to be able to 
# register the Flow env for this experiment
create_env, gym_name = make_create_env(params=flow_params, version=0)

# Register as rllib env with Gym
register_env(gym_name, create_env)




trials = run_experiments({
    flow_params["exp_tag"]: {
        "run": alg_run,
        "env": gym_name,
        "config": {
            **config
        },
        "checkpoint_freq": 1,  # number of iterations between checkpoints
        "checkpoint_at_end": True,  # generate a checkpoint at the end
        "max_failures": 999,
        "stop": {  # stopping conditions
            "training_iteration": 1000,  # number of iterations to stop after
        },
        "restore" : "~/ray_results/traffic_light_grid/PPO_TrafficLightGridPOEnv-v0_454c58c2_2020-12-10_11-17-599arcpty3/checkpoint_36/checkpoint-36"
    },
})

