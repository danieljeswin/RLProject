from flow.networks import RingNetwork
from flow.core.params import InitialConfig, NetParams
from flow.networks.ring import ADDITIONAL_NET_PARAMS
from flow.core.params import VehicleParams, SumoParams, EnvParams
from flow.controllers import IDMController, RLController, ContinuousRouter
from flow.envs import WaveAttenuationPOEnv

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

N_CPUS = 2
N_ROLLOUTS = 1
HORIZON = 100
ray.init(num_cpus = N_CPUS)


network_name = RingNetwork
name = "rllib_example"
net_params = NetParams(additional_params = ADDITIONAL_NET_PARAMS)
initial_config = InitialConfig(spacing = "uniform", perturbation = 1)
vehicles = VehicleParams()
vehicles.add(veh_id = "human", acceleration_controller = (IDMController, {}),
    routing_controller = (ContinuousRouter, {}), num_vehicles = 21)
vehicles.add(veh_id = "rl", acceleration_controller = (RLController, {}),
    routing_controller = (ContinuousRouter, {}), num_vehicles = 1)


sim_params = SumoParams(sim_step = 0.1, render = False)
env_params = EnvParams(horizon = HORIZON, additional_params = {
    'max_accel': 1,
    'max_decel': 1,
    'ring_length': [220, 270],
},)

env_name = WaveAttenuationPOEnv

flow_params = dict(
    exp_tag = name,
    env_name = env_name,
    network = network_name,
    simulator = 'traci',
    sim = sim_params,
    env = env_params,
    net = net_params,
    veh = vehicles,
    initial = initial_config
)




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
config["model"].update({"fcnet_hiddens": [16, 16]})  # size of hidden layers in network
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
            "training_iteration": 1,  # number of iterations to stop after
        },
    },
})
