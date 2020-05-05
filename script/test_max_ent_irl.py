import time

import matplotlib.pyplot as plt
import numpy as np

from grid_world import GridWorld
from max_ent_irl import MaxEntIRL
from util.dataset import collect_trajectories
from util.mdp import q_learning, value_iteration
from util.plotting import plot_grid_map, plot_policy
from util.policy import *
from util.reward import construct_goal_reward, construct_human_radius_reward


def test_gridworld_maxent_irl():
    np.random.seed(0)

    # env
    N = 10
    goal_pos = np.array([[N-1, N-1], [N-1, N-2], [N-1, N-3], [N-1, N-4], [N-1, N-5]])
    human_pos = np.array([[N//2, N//2]])
    human_radius = 3

    grid = np.zeros((N, N), dtype=float)
    grid = construct_goal_reward(grid, goal_pos, 10)
    grid = construct_human_radius_reward(grid, human_pos, human_radius, -10)

    env = GridWorld(
        dimensions=(N, N),
        init_pos=(0, 0),
        goal_pos=goal_pos,
        reward_grid=grid,
        human_pos=human_pos,
        action_success_rate=1,
        render=True,
    )

    # learn a policy
    # mdp_algo = q_learning(env.transition, env.reward, gamma=0.99)
    mdp_algo = value_iteration(env.transition, env.reward, gamma=0.99)
    # policy = EpsGreedyPolicy(env.action_space(), mdp_algo, epsilon=0.1)
    policy = StochasticGreedyPolicy(
        env.action_space(), mdp_algo, env.transition)
    # policy = GreedyPolicy(env.action_space(), mdp_algo)

    V = np.asarray(mdp_algo.V).reshape((N, N)).T
    R = env.reward.reshape((N, N)).T
    plot_grid_map(R, "Reward (Ground Truth)", cmap=plt.cm.Reds)
    plot_grid_map(V, "Value Function", cmap=plt.cm.Blues)

    # roll out trajectories
    dataset = collect_trajectories(
        policy=policy,
        env=env,
        num_trajectories=20,
        maxlen=30)

    dataset_state_dist = np.zeros(env.observation_space().n)
    for t in dataset:
        for trans in t:
            dataset_state_dist[trans.obs] += 1
    dataset_density = dataset_state_dist / np.sum(dataset_state_dist)
    dataset_density = dataset_density.reshape((N, N)).T
    plot_grid_map(
        dataset_density, "Dataset State Distribution", print_values=True)
    # plt.show()

    # phi
    phi = [env._feature_map(s) for s in range(env.observation_space().n)]
    phi = np.array(phi)

    # IRL
    me_irl = MaxEntIRL(
        observation_space=env.observation_space(),
        action_space=env.action_space(),
        transition=env.transition,
        goal_states=env.goal_states,
        dataset=dataset,
        feature_map=phi,
        max_iter=10,
        anneal_rate=0.9)
    Rprime = me_irl.train()
    Rprime = Rprime.reshape((N, N)).T

    # plot results
    plot_grid_map(Rprime, "Reward (IRL)", print_values=True, cmap=plt.cm.Blues)
    plt.show()


if __name__ == '__main__':
    test_gridworld_maxent_irl()
