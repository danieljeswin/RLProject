# the TestEnv environment is used to simply simulate the network
from flow.envs import TestEnv

# the Experiment class is used for running simulations
from flow.core.experiment import Experiment

# all other imports are standard
from flow.core.params import VehicleParams
from flow.core.params import NetParams
from flow.core.params import InitialConfig
from flow.core.params import EnvParams
from flow.core.params import SumoParams

from flow.networks import Network

net_params = NetParams(
    osm_path='map.osm'
)

# create the remainding parameters
env_params = EnvParams()
sim_params = SumoParams(render=True)
initial_config = InitialConfig()
vehicles = VehicleParams()
vehicles.add('human', num_vehicles=1000)

flow_params = dict(
    exp_tag='bay_bridge',
    env_name=TestEnv,
    network=Network,
    simulator='traci',
    sim=sim_params,
    env=env_params,
    net=net_params,
    veh=vehicles,
    initial=initial_config,
)

# number of time steps
flow_params['env'].horizon = 100000
exp = Experiment(flow_params)

# run the sumo simulation
_ = exp.run(1)




# # we define an EDGES_DISTRIBUTION variable with the edges within 
# # the westbound Bay Bridge 
# EDGES_DISTRIBUTION = [
#     "11197898",
#     "123741311", 
#     "123741303",
#     "90077193#0",
#     "90077193#1", 
#     "340686922", 
#     "236348366", 
#     "340686911#0",
#     "340686911#1",
#     "340686911#2",
#     "340686911#3",
#     "236348361", 
#     "236348360#0", 
#     "236348360#1"
# ]

# the above variable is added to initial_config
# new_initial_config = InitialConfig(
#     spacing="random",
#     edges_distribution=EDGES_DISTRIBUTION
# )

# class BayBridgeOSMNetwork(Network):

#     def specify_routes(self, net_params):
#         return {
#             "11197898": [
#                 "11197898", "123741311", "123741303", "90077193#0", "90077193#1", 
#                 "340686922", "236348366", "340686911#0", "340686911#1",
#                 "340686911#2", "340686911#3", "236348361", "236348360#0", "236348360#1",
#             ],
#             "123741311": [
#                 "123741311", "123741303", "90077193#0", "90077193#1", "340686922", 
#                 "236348366", "340686911#0", "340686911#1", "340686911#2",
#                 "340686911#3", "236348361", "236348360#0", "236348360#1"
#             ],
#             "123741303": [
#                 "123741303", "90077193#0", "90077193#1", "340686922", "236348366",
#                 "340686911#0", "340686911#1", "340686911#2", "340686911#3", "236348361",
#                 "236348360#0", "236348360#1"
#             ],
#             "90077193#0": [
#                 "90077193#0", "90077193#1", "340686922", "236348366", "340686911#0",
#                 "340686911#1", "340686911#2", "340686911#3", "236348361", "236348360#0",
#                 "236348360#1"
#             ],
#             "90077193#1": [
#                 "90077193#1", "340686922", "236348366", "340686911#0", "340686911#1",
#                 "340686911#2", "340686911#3", "236348361", "236348360#0", "236348360#1"
#             ],
#             "340686922": [
#                 "340686922", "236348366", "340686911#0", "340686911#1", "340686911#2",
#                 "340686911#3", "236348361", "236348360#0", "236348360#1"
#             ],
#             "236348366": [
#                 "236348366", "340686911#0", "340686911#1", "340686911#2", "340686911#3",
#                 "236348361", "236348360#0", "236348360#1"
#             ],
#             "340686911#0": [
#                 "340686911#0", "340686911#1", "340686911#2", "340686911#3", "236348361",
#                 "236348360#0", "236348360#1"
#             ],
#             "340686911#1": [
#                 "340686911#1", "340686911#2", "340686911#3", "236348361", "236348360#0",
#                 "236348360#1"
#             ],
#             "340686911#2": [
#                 "340686911#2", "340686911#3", "236348361", "236348360#0", "236348360#1"
#             ],
#             "340686911#3": [
#                 "340686911#3", "236348361", "236348360#0", "236348360#1"
#             ],
#             "236348361": [
#                 "236348361", "236348360#0", "236348360#1"
#             ],
#             "236348360#0": [
#                 "236348360#0", "236348360#1"
#             ],
#             "236348360#1": [
#                 "236348360#1"
#             ]
#         }

# flow_params = dict(
# exp_tag='bay_bridge',
# env_name=TestEnv,
# network=BayBridgeOSMNetwork,
# simulator='traci',
# sim=sim_params,
# env=env_params,
# net=net_params,
# veh=vehicles,
# initial=new_initial_config,
# )

# # number of time steps
# flow_params['env'].horizon = 10000
# exp = Experiment(flow_params)

# # run the sumo simulation
# _ = exp.run(1)   