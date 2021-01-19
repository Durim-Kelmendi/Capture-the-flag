"""The file initiaizes sound."""
import pygame
import os

pygame.mixer.init()

wood_destruction = pygame.mixer.Sound("sound/Wood.wav")
shoot = pygame.mixer.Sound("sound/Shoot.wav")
victory = pygame.mixer.Sound("sound" + os.sep + "Victory_new.wav")
