import sys
import os
import importlib
import threading
import queue
import pygame
import json
import random
import time

from genetic_algorithm import GeneticAlgorithm
from hill_climbing import ParallelHillClimbing
from SimulatedAnnealing import SimulatedAnnealing

from game_classes import (
    Game, Tower, Mortar, CrossbowTower, screen, clock, fps, WHITE, TEAL, 
    screen_width, screen_height, draw_health_bar, path_groups, map_data, 
    grid_size, grid_data, grid_width, grid_height , RED, BLACK, draw_paths, Enemy, Archer, Giant, 
    GREEN, GRAY, BLUE, DARK_BLUE, LIGHT_BLUE, ORANGE, PURPLE,
)



def print_game_over():
    screen.fill(WHITE)
    font = pygame.font.Font(None, 74)
    text_surface = font.render("Game Over", True, RED)
    text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text_surface, text_rect)
    pygame.display.update()
    pygame.time.wait(2000)

def draw_button(screen, text, font, color, rect):
    pygame.draw.rect(screen, color, rect)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

def game_introduction(game):
    intro_running = True
    while intro_running:
        screen.fill(WHITE)
        font = pygame.font.Font(None, 22)
        introduction_text = [
            "Welcome to the Tower Defense Game!",
            "Objective: Protect your main tower from enemy attacks.",
            "Use towers, mortars, and crossbow towers to defend against enemies.",
            "Click to place towers: Left Click for Tower, Right Click for Mortar, Middle Click for Crossbow Tower.",
            "Survive as long as you can!",
            "",
            "Game Elements:",
            "RED Enemy: Basic attacking unit that moves towards the main tower and deals damage.",
            "PURPLE Archer: Ranged unit that attacks from a distance and can hit multiple targets.",
            "ORANGE Giant: High health unit that deals heavy damage to towers and the main tower.",
            "BLUE Tower: Basic defensive structure that attacks enemies within its range.",
            "LIGHT_BLUE Crossbow Tower: Fast-attacking tower with a shorter range and lower damage.",
            "DARK_BLUE Mortar: Long-range tower that deals area damage but damages itself over time.",
            "GREEN Main Tower: The central structure you must protect from enemy attacks."
        ]
        for i, line in enumerate(introduction_text):
            if i > 6:  # Renkli satırlar için
                color_name, text = line.split(' ', 1)  # Renk ve metni ayır
                color = eval(color_name)  # Rengi al
                text_surface = font.render(text, True, color)
            else:
                text_surface = font.render(line, True, BLACK)  # Normal siyah metin
            screen.blit(text_surface, (50, 50 + i * 40))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    intro_running = False  # Enter tuşuna basıldığında döngüyü durdur

        pygame.display.update()  # Ekranı güncelle
        clock.tick(fps)  # FPS'yi ayarla

def main_menu(game):

    menu_running = True

    while menu_running:
        screen.fill(WHITE)
        font = pygame.font.Font(None, 74)
        title_surface = font.render("Tower Defense Game", True, BLUE)
        title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 4))
        screen.blit(title_surface, title_rect)

        font = pygame.font.Font(None, 36)
        play_button = pygame.Rect(screen_width // 2 - 300, screen_height // 2 - 50, 200, 50)
        intro_button = pygame.Rect(screen_width // 2 - 0, screen_height // 2 - 50, 200, 50)
        ga_button = pygame.Rect(screen_width // 2 - 300, screen_height // 2 + 50, 200, 50)
        phc_button = pygame.Rect(screen_width // 2 - 0, screen_height // 2 + 50, 200, 50)
        sa_button = pygame.Rect(screen_width // 2 - 200, screen_height // 2 + 150, 350, 50)

        draw_button(screen, "Play Game", font, TEAL, play_button)
        draw_button(screen, "Introduction", font, TEAL, intro_button)
        draw_button(screen, "Run GA", font, TEAL, ga_button)
        draw_button(screen, "Run Parallel HC", font, TEAL, phc_button)
        draw_button(screen, "Run Simulated Annealing", font, TEAL, sa_button)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    game.reset()
                    main_game(game)
                    menu_running = False
                elif intro_button.collidepoint(event.pos):
                    game_introduction(game)
                elif ga_button.collidepoint(event.pos):
                    run_genetic_algorithm()
                elif phc_button.collidepoint(event.pos):
                    run_parallel_hill_climbing()
                elif sa_button.collidepoint(event.pos):
                    run_simulated_annealing()


        pygame.display.update()
        clock.tick(fps)




def main_game(game):
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_x // grid_size, mouse_y // grid_size
                if (grid_x, grid_y) not in grid_data and not any(t.x == grid_x and t.y == grid_y for t in game.towers + game.mortars + game.crossbow_towers):
                    if event.button == 1 and game.money >= Tower(grid_x, grid_y).cost:  # Sol tıkla normal kule yerleştir
                        game.towers.append(Tower(grid_x, grid_y))
                        game.money -= Tower(grid_x, grid_y).cost  # Kule yerleştirildiğinde para azaltılır
                    elif event.button == 3 and game.money >= Mortar(grid_x, grid_y).cost:  # Sağ tıkla havan yerleştir
                        game.mortars.append(Mortar(grid_x, grid_y))
                        game.money -= Mortar(grid_x, grid_y).cost  # Havan yerleştirildiğinde para azaltılır
                    elif event.button == 2 and game.money >= CrossbowTower(grid_x, grid_y).cost:  # Orta tıkla arbalet kulesi yerleştir
                        game.crossbow_towers.append(CrossbowTower(grid_x, grid_y))
                        game.money -= CrossbowTower(grid_x, grid_y).cost  # Arbalet kulesi yerleştirildiğinde para azaltılır

        game.enemies = [enemy for enemy in game.enemies if enemy.health > 0]
        game.towers = [tower for tower in game.towers if tower.health > 0]
        game.mortars = [mortar for mortar in game.mortars if mortar.health > 0]
        game.crossbow_towers = [crossbow_tower for crossbow_tower in game.crossbow_towers if crossbow_tower.health > 0]

        game.survival_time += 1 / fps  # Hayatta kalınan süreyi artır
        game.update_score()
        game.spawn_counter += 1
        if game.spawn_counter % game.giant_spawn_frequency == 0:
            game.spawn_giant()
        elif game.spawn_counter % game.archer_spawn_frequency == 0:
            game.spawn_archer()
        elif game.spawn_counter % game.spawn_frequency == 0:
            game.spawn_enemy()

        screen.fill(WHITE)
        for path_group in path_groups:
            draw_paths(path_group)
        game.main_tower.draw()
        game.main_tower.attack(game.enemies)
        for tower in game.towers:
            tower.draw()
            tower.attack(game.enemies)
        for mortar in game.mortars:
            mortar.draw()
            mortar.update()
            mortar.attack(game.enemies)
        for crossbow_tower in game.crossbow_towers:
            crossbow_tower.draw()
            crossbow_tower.attack(game.enemies)
        for enemy in game.enemies:
            enemy.move(game)
            enemy.draw()

        if game.main_tower.health <= 0:
            print_game_over()
            main_menu(game)
            return

        game.draw_hud()  # HUD'yi ekrana çiz
        
        pygame.display.update()
        clock.tick(fps)



"""
def main_game(game):
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_x // grid_size, mouse_y // grid_size
                if (grid_x, grid_y) not in grid_data and not any(t.x == grid_x and t.y == grid_y for t in game.towers + game.mortars + game.crossbow_towers):
                    if event.button == 1 and game.money >= Tower(grid_x, grid_y).cost:  # Sol tıkla normal kule yerleştir
                        game.towers.append(Tower(grid_x, grid_y))
                        game.money -= Tower(grid_x, grid_y).cost  # Kule yerleştirildiğinde para azaltılır
                    elif event.button == 3 and game.money >= Mortar(grid_x, grid_y).cost:  # Sağ tıkla havan yerleştir
                        game.mortars.append(Mortar(grid_x, grid_y))
                        game.money -= Mortar(grid_x, grid_y).cost  # Havan yerleştirildiğinde para azaltılır
                    elif event.button == 2 and game.money >= CrossbowTower(grid_x, grid_y).cost:  # Orta tıkla arbalet kulesi yerleştir
                        game.crossbow_towers.append(CrossbowTower(grid_x, grid_y))
                        game.money -= CrossbowTower(grid_x, grid_y).cost  # Arbalet kulesi yerleştirildiğinde para azaltılır

        game.enemies = [enemy for enemy in game.enemies if enemy.health > 0]
        game.towers = [tower for tower in game.towers if tower.health > 0]
        game.mortars = [mortar for mortar in game.mortars if mortar.health > 0]
        game.crossbow_towers = [crossbow_tower for crossbow_tower in game.crossbow_towers if crossbow_tower.health > 0]

        game.survival_time += 1 / fps  # Hayatta kalınan süreyi artır
        game.update_score()
        game.spawn_counter += 1
        if game.spawn_counter % game.giant_spawn_frequency == 0:
            game.spawn_giant()
        elif game.spawn_counter % game.archer_spawn_frequency == 0:
            game.spawn_archer()
        elif game.spawn_counter % game.spawn_frequency == 0:
            game.spawn_enemy()

        screen.fill(WHITE)
        for path_group in path_groups:
            draw_paths(path_group)
        game.main_tower.draw()
        game.main_tower.attack(game.enemies)
        for tower in game.towers:
            tower.draw()
            tower.attack(game.enemies)
        for mortar in game.mortars:
            mortar.draw()
            mortar.update()
            mortar.attack(game.enemies)
        for crossbow_tower in game.crossbow_towers:
            crossbow_tower.draw()
            crossbow_tower.attack(game.enemies)
        for enemy in game.enemies:
            enemy.move(game)
            enemy.update()  # Animasyonu güncelle
            enemy.draw()

        if game.main_tower.health <= 0:
            print_game_over()
            main_menu(game)
            return

        game.draw_hud()  # HUD'yi ekrana çiz
        
        pygame.display.update()
        clock.tick(fps)
    
"""
def run_genetic_algorithm():
    global ga
    ga = GeneticAlgorithm(population_size=10, mutation_rate=0.1, generations=10, game_class=Game)
    ga.evolve()


def run_parallel_hill_climbing():
    global phc
    phc = ParallelHillClimbing(num_threads=1, restarts=5, game_class=Game)
    best_instance, best_fitness = phc.run(visualize=True)
    print("Parallel Hill Climbing Best Fitness:", best_fitness)
    phc.visualize_game(best_instance, 0)


# Çalıştırmak için kullanılan fonksiyon
def run_simulated_annealing():
    global sa
    sa = SimulatedAnnealing(initial_temp=1000, cooling_rate=0.95, game_class=Game)
    best_instance, best_fitness = sa.run(visualize=True)
    print("Simulated Annealing Best Fitness:", best_fitness)
       
if __name__ == "__main__": 
    # Oyunu başlat
    game_instance = Game()
    main_menu(game_instance)