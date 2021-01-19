import pygame
import os

main_dir = os.path.split(os.path.abspath(__file__))[0]

pygame.mixer.init()

wood_destruction = pygame.mixer.Sound("sound/Wood.wav")
shoot = pygame.mixer.Sound("sound/Shoot.wav")
