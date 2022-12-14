# -*- coding: UTF-8 -*-
import numpy as np
import random
import copy

# from render import Render
MAZE = np.array([
    ['1', ' ', ' ', ' ', ' ', '2', 'X', ' ', ' ', ' ', ' ', ' ', 'G'],
    [' ', ' ', ' ', ' ', ' ', ' ', 'X', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', '1', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', 'X', ' ', ' ', ' ', ' ', ' ', ' '],
    ['2', ' ', ' ', ' ', ' ', '3', 'X', ' ', ' ', ' ', ' ', ' ', ' '],
    ['X', 'X', '3', ' ', 'X', 'X', 'X', 'X', 'X', ' ', '1', 'X', 'X'],
    [' ', ' ', ' ', ' ', ' ', ' ', 'X', '2', ' ', ' ', ' ', ' ', '3'],
    [' ', ' ', ' ', ' ', ' ', ' ', 'X', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', '2', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', 'X', ' ', ' ', ' ', ' ', ' ', ' '],
    ['_', ' ', ' ', ' ', ' ', ' ', 'X', '3', ' ', ' ', ' ', ' ', '1']])
REWARDS = dict(zip(['1', '2', '3'], list([1.0, 0.5, -1.0])))


class FourRoom:
    """
    A discretized version of the gridworld environment introduced in [1]. Here, an agent learns to
    collect shapes with positive reward, while avoid those with negative reward, and then travel to a fixed goal.
    The gridworld is split into four rooms separated by walls with passage-ways.

    # Code adaptaed from: https://github.com/mike-gimelfarb/deep-successor-features-for-transfer/blob/main/source/tasks/gridworld.py

    In this version, a render is implemented and the agent can start at random locations.

    References
    ----------
    [1] Barreto, Andr�, et al. "Successor Features for Transfer in Reinforcement Learning." NIPS. 2017.
    """

    LEFT, UP, RIGHT, DOWN = 0, 1, 2, 3

    def __init__(self, maze=MAZE, shape_rewards=REWARDS, random_initial_position=True):
        """
        Creates a new instance of the shapes environment.

        Parameters
        ----------
        maze : np.ndarray
            an array of string values representing the type of each cell in the environment:
                G indicates a goal state (terminal state)
                _ indicates an initial state (there can be multiple, and one is selected at random
                    at the start of each episode)
                X indicates a barrier
                0, 1, .... 9 indicates the type of shape to be placed in the corresponding cell
                entries containing other characters are treated as regular empty cells
        shape_rewards : dict
            a dictionary mapping the type of shape (0, 1, ... ) to a corresponding reward to provide
            to the agent for collecting an object of that type
        """
        self.max_num_agents = 1
        self.my_render = None
        self.random_initial_position = random_initial_position

        # self.action_spaces[agent].n

        self.height, self.width = maze.shape
        self.maze = maze
        self.env_maze = copy.deepcopy(self.maze)
        self.shape_rewards = shape_rewards
        shape_types = sorted(list(shape_rewards.keys()))
        self.all_shapes = dict(zip(shape_types, range(len(shape_types))))

        self.goal = None
        self.initial = []
        self.occupied = set()
        self.shape_ids = dict()
        for c in range(self.width):
            for r in range(self.height):
                if maze[r, c] == 'G':
                    self.goal = (r, c)
                elif maze[r, c] == '_':
                    self.initial.append((r, c))
                elif maze[r, c] == 'X':
                    self.occupied.add((r, c))
                elif maze[r, c] in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
                    self.shape_ids[(r, c)] = len(self.shape_ids)

        self.state = None
        self.render_flag = None

    def clone(self):
        return FourRoom(self.maze, self.shape_rewards)

    def initialize(self, render_flag=False):
        self.render_flag = render_flag
        self.env_maze = copy.deepcopy(self.maze)
        if self.random_initial_position:
            for (r, c) in self.initial:
                self.env_maze[r, c] = ' '
            self.initial = []
            n_r, n_c = np.shape(self.maze)
            initial_position = False
            while not initial_position:
                r, c = (np.random.randint(0, n_r), np.random.randint(0, n_c))
                if self.maze[r, c] == ' ':
                    self.initial.append((r, c))
                    self.env_maze[r, c] = '_'
                    initial_position = True
        self.state = (random.choice(self.initial), tuple(0 for _ in range(len(self.shape_ids))))
        # self.state = ((r,c), tuple(0 for _ in range(len(self.shape_ids))))
        # if render_flag:
        #     self.my_render = Render(maze=self.env_maze)
        return self.state

    def action_count(self):
        return 4

    def transition(self, action):
        (row, col), collected = self.state
        # print(self.state)
        # print(action)
        # perform the movement
        if action == FourRoom.LEFT:
            col -= 1
        elif action == FourRoom.UP:
            row -= 1
        elif action == FourRoom.RIGHT:
            col += 1
        elif action == FourRoom.DOWN:
            row += 1
        else:
            raise Exception('bad action {}'.format(action))

        # out of bounds, cannot move
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return self.state, 0., False

        # into a blocked cell, cannot move
        s1 = (row, col)
        if s1 in self.occupied:
            return self.state, 0., False

        # can now move
        self.state = (s1, collected)

        # into a goal cell
        if s1 == self.goal:
            return self.state, 1., True

        # into a shape cell
        if s1 in self.shape_ids:
            shape_id = self.shape_ids[s1]
            if collected[shape_id] == 1:

                # already collected this flag
                return self.state, 0., False
            else:

                # collect the new flag
                collected = list(collected)
                collected[shape_id] = 1
                collected = tuple(collected)
                self.state = (s1, collected)
                reward = self.shape_rewards[self.maze[row, col]]
                return self.state, reward, False

        # into an empty cell
        return self.state, 0., False

    def render(self, obs):
        if self.render_flag:
            self.my_render.update(obs)

    # def reset(self):
    #     self.my_render = Render(maze=self.maze)