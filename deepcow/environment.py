from deepcow.constant import *
from deepcow.entity import *
from deepcow.actions import *
from pygame.math import Vector2
import os
import pygame
import numpy as np

GRAY = (200, 200, 200)


class Environment(object):
    def __init__(self,
                 cow_count=1,
                 cow_ray_count=20,
                 cow_field_of_view=100,
                 cow_ray_length=300,
                 cow_mass=2.0,
                 wolf_ray_count=20,
                 wolf_field_of_view=100,
                 wolf_ray_length=300,
                 wolf_count=1,
                 wolf_mass=2.0,
                 grass_count=1,
                 delta_time=1.0 / 60.0,
                 game_width=800,
                 game_height=600,
                 draw=True):
        # Center the initial pygame windows
        pos_x = 100  # screen_width / 2 - window_width / 2
        pos_y = 100  # screen_height - window_height
        os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % (pos_x, pos_y)
        os.environ['SDL_VIDEO_CENTERED'] = '0'

        # initialize pygame and set set surface parameters
        pygame.init()
        self.draw = draw
        if draw:
            self.screen = pygame.display.set_mode((game_width, game_height))
            pygame.display.set_caption('Cow Simulator')

        # initialize agents
        self.cows = [Agent(mass=cow_mass,
                           ray_count=cow_ray_count,
                           field_of_view=cow_field_of_view,
                           ray_length=cow_ray_length,
                           color=(150, 75, 0)) for x in range(cow_count)]
        self.wolves = [Agent(mass=wolf_mass,
                             ray_count=wolf_ray_count,
                             field_of_view=wolf_field_of_view,
                             ray_length=wolf_ray_length,
                             color=(25, 25, 112)) for x in range(wolf_count)]
        self.agents = self.cows + self.wolves

        # initialize entities
        self.grass = [Entity(color=(0, 255, 0)) for x in range(grass_count)]
        self.entities = self.agents + self.grass

        # gameloop
        self.delta_time = delta_time  # "deltatime", set it to passed time between each frame to have per second movement
        self.reset()

    def reset(self) -> [State]:
        for entity in self.entities:
            entity.reset()
        states, _, _ = self.step([Action.NOTHING for agent in self.agents])
        return states

    def __perform_actions(self, actions: [Action]) -> None:
        assert len(actions) == len(self.agents)
        for i in range(0, len(actions)):
            self.agents[i].perform_action(self.delta_time, actions[i])

    def __update_agents_positions(self):
        for agent in self.agents:
            agent.update_position(self.delta_time)
        for agent in self.agents:
            agent.calculate_agents_collisions(agents=self.agents)
        for agent in self.agents:
            agent.calculate_border_collisions()

    def __eat(self, agents: [Agent], foods: [Entity]) -> (np.ndarray, bool):
        rewards = np.empty(len(agents))
        done = False
        for index, agent in enumerate(agents):
            reward, eaten = agent.eat(foods, self.delta_time)
            rewards[index] = reward + eaten * 10
            if eaten != 0:
                done = True
        return rewards, done

    def __perceive(self) -> [State]:
        return [agent.perceive(self.entities) for agent in self.agents]

    def step(self, actions: [Action]) -> ([State], [float], bool):
        self.__perform_actions(actions)
        self.__update_agents_positions()
        states = self.__perceive()
        rewards, done = self.__eat(self.cows, self.grass)
        if self.draw:
            self.__draw_environment()
        return states, rewards, done

    def __draw_environment(self, draw_perception=True, draw_entity_information=True):
        self.screen.fill(GRAY)
        if draw_perception:
            for grass in self.grass:
                grass.draw(screen=self.screen)
            for agent in self.agents:
                agent.draw_perception(screen=self.screen)
                agent.draw(screen=self.screen)
        else:
            for entity in self.entities:
                entity.draw(screen=self.screen)
        if draw_entity_information:
            for i, entity in enumerate(self.entities, start=0):
                entity.draw_information(self.screen, i)
        pygame.display.update()

    def quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
