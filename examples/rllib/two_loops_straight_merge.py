"""
(description)
"""
import cloudpickle
import gym
import numpy as np

import ray
import ray.rllib.ppo as ppo
from ray.tune.registry import get_registry, register_env as register_rllib_env
from ray.rllib.models import ModelCatalog

from flow.core.util import register_env
from flow.utils.tuple_preprocessor import TuplePreprocessor

from flow.core.params import SumoParams, EnvParams, InitialConfig, NetParams
from flow.core.params import SumoCarFollowingParams, SumoLaneChangeParams
from flow.core.vehicles import Vehicles

from flow.controllers.rlcontroller import RLController
from flow.controllers.car_following_models import *
from flow.controllers.lane_change_controllers import *
from flow.controllers.routing_controllers import ContinuousRouter

from flow.scenarios.two_loops_one_merging_new.gen import TwoLoopOneMergingGenerator
from flow.scenarios.two_loops_one_merging_new.scenario \
    import TwoLoopsOneMergingScenario


def make_create_env(flow_env_name, version):
    env_name = flow_env_name+'-v%s' % version

    def create_env():
        # Experiment prefix
        exp_tag = "two_loops_straight_merge_example"

        import flow.envs as flow_envs
        sumo_params = SumoParams(sim_step=0.1, sumo_binary="sumo")

        # note that the vehicles are added sequentially by the generator,
        # so place the merging vehicles after the vehicles in the ring
        vehicles = Vehicles()
        vehicles.add_vehicles(veh_id="human",
                              acceleration_controller=(
                                    IDMController, {"noise": 0.2}),
                              lane_change_controller=(
                                    SumoLaneChangeController, {}),
                              routing_controller=(ContinuousRouter, {}),
                              num_vehicles=6,
                              sumo_car_following_params=SumoCarFollowingParams(
                                  minGap=0.0, tau=0.5),
                              sumo_lc_params=SumoLaneChangeParams())

        vehicles.add_vehicles(veh_id="merge-rl",
                              acceleration_controller=(
                                RLController, {"fail_safe": "safe_velocity"}),
                              lane_change_controller=(
                                SumoLaneChangeController, {}),
                              routing_controller=(ContinuousRouter, {}),
                              speed_mode="no_collide",
                              num_vehicles=10,
                              sumo_car_following_params=SumoCarFollowingParams(
                                  minGap=0.01, tau=0.5),
                              sumo_lc_params=SumoLaneChangeParams())

        additional_env_params = {"target_velocity": 20, "max-deacc": -1.5,
                                 "max-acc": 1, "num_steps": 1000}
        env_params = EnvParams(additional_params=additional_env_params)

        additional_net_params = {"ring_radius": 50, "lanes": 1,
                                 "lane_length": 75, "speed_limit": 30,
                                 "resolution": 40}
        net_params = NetParams(
            no_internal_links=False,
            additional_params=additional_net_params
        )

        initial_config = InitialConfig(
            x0=50,
            spacing="custom",
            additional_params={"merge_bunching": 0}
        )

        scenario = TwoLoopsOneMergingScenario(
            name=exp_tag,
            generator_class=TwoLoopOneMergingGenerator,
            vehicles=vehicles,
            net_params=net_params,
            initial_config=initial_config
        )

        pass_params = (flow_env_name, sumo_params, vehicles, env_params,
                       net_params, initial_config, scenario, version)

        register_env(*pass_params)
        env = gym.envs.make(env_name)

        env.observation_space.shape = (
            int(np.sum([c.shape for c in env.observation_space.spaces])),)

        ModelCatalog.register_preprocessor(env_name, TuplePreprocessor)

        return env
    return create_env, env_name

if __name__ == "__main__":
    config = ppo.DEFAULT_CONFIG.copy()
    horizon = 1000  # FIXME(cathywu) streamline; need to manually match above
    num_cpus = 3
    n_rollouts = 30

    ray.init(num_cpus=num_cpus, redirect_output=True)
    # ray.init(redis_address="172.31.92.24:6379", redirect_output=True)

    config["num_workers"] = num_cpus
    config["timesteps_per_batch"] = horizon * n_rollouts
    config["gamma"] = 0.999  # discount rate

    config["lambda"] = 0.97
    config["sgd_batchsize"] = min(16 * 1024, 1024 * num_cpus)
    config["kl_target"] = 0.02
    config["num_sgd_iter"] = 10
    config["horizon"] = horizon

    # Two-level policy parameters
    config["model"].update(
        {"fcnet_hiddens": [[32, 32]] * 2})
    config["model"]["user_data"] = {}
    config["model"]["user_data"].update({"num_subpolicies": 2,
                                         "fn_choose_subpolicy": list(
                                             cloudpickle.dumps(lambda x: 0))})

    flow_env_name = "TwoLoopsMergeEnv"
    create_env, env_name = make_create_env(flow_env_name, 0)

    # Register as rllib env
    register_rllib_env(env_name, create_env)

    alg = ppo.PPOAgent(env=env_name, registry=get_registry(), config=config)
    for i in range(2):
        alg.train()
        if i % 20 == 0:
            alg.save()  # save checkpoint
