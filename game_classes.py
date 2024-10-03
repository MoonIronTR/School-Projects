import pygame
import json
import sys
import os
"""

# Pygame başlatma ve ekran ayarları
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))

# Renk tanımları
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
DARK_BLUE = (0, 0, 139)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
TEAL = (0, 128, 128)
BLACK = (0, 0, 0)

# Zaman ve FPS ayarları
clock = pygame.time.Clock()
fps = 60

# Grid ayarları
grid_size = 20
grid_width = screen_width // grid_size
grid_height = screen_height // grid_size



def load_sprites(sprite_sheet, frame_width, frame_height):
    sheet = pygame.image.load(sprite_sheet).convert_alpha()
    sheet_width, sheet_height = sheet.get_size()
    sprites = []

    for y in range(0, sheet_height, frame_height):
        for x in range(0, sheet_width, frame_width):
            if x + frame_width <= sheet_width and y + frame_height <= sheet_height:
                frame = sheet.subsurface((x, y, frame_width, frame_height))
                sprites.append(frame)

    return sprites

def load_individual_sprites(sprite_files, frame_width, frame_height):
    sprites = []
    for file in sprite_files:
        sprite = pygame.image.load(file).convert_alpha()
        sprite = pygame.transform.scale(sprite, (frame_width, frame_height))
        sprites.append(sprite)
    return sprites


def draw_health_bar(screen, position, health, max_health, width, height):
    pygame.draw.rect(screen, (128, 128, 128), (position[0], position[1] - 10, width, height))
    current_health_width = (health / max_health) * width
    pygame.draw.rect(screen, ORANGE, (position[0], position[1] - 10, current_health_width, height))

def load_map_data(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return {(int(item[0]), int(item[1])): item[2] for item in data}

def find_path_starts_and_ends(grid_data):
    path_starts = {}
    path_ends = {}
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for (x, y), color in grid_data.items():
        if color == "grey":
            neighbors = [(x + dx, y + dy) for dx, dy in directions]
            neighbor_colors = [grid_data.get((x + dx, y + dy), "white") for dx, dy in directions]
            if neighbor_colors.count("grey") == 1 and neighbor_colors.count("white") == 3:
                path_starts[(x, y)] = True
            if neighbor_colors.count("grey") == 1 and neighbor_colors.count("green") == 1 and neighbor_colors.count("white") == 2:
                path_ends[(x, y)] = True

    return path_starts, path_ends

def find_paths(grid_data, path_starts):
    visited = set()
    paths = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def dfs(start):
        stack = [start]
        path = []
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                path.append(current)
                for dx, dy in directions:
                    neighbor = (current[0] + dx, current[1] + dy)
                    if grid_data.get(neighbor, None) == 'grey' and neighbor not in visited:
                        stack.append(neighbor)
        return path

    for start in path_starts:
        if start not in visited:
            path = dfs(start)
            if path:
                paths.append(path)

    return paths

map_data = load_map_data("map.json")
grid_data = {(x // grid_size, y // grid_size): color for (x, y), color in map_data.items()}
path_starts, path_ends = find_path_starts_and_ends(grid_data)
paths = find_paths(grid_data, path_starts)
path_groups = [paths[i::3] for i in range(3)]

def draw_paths(paths):
    for path in paths:
        for x, y in path:
            rect = pygame.Rect(x * grid_size, y * grid_size, grid_size, grid_size)
            pygame.draw.rect(screen, GRAY, rect)

class Game:
    def __init__(self):
        self.enemy_sprites = load_sprites('sprites/enemies/militaWarrior.png', 32, 32)  # Animasyonlu sprite'ları yükle
        self.archer_run_sprites = load_individual_sprites([
            f'sprites/archers/archer_run{i}.png' for i in range(1, 11)
        ], 32, 32)
        self.archer_attack_sprites = load_individual_sprites([
            f'sprites/archers/archer_attack{i}.png' for i in range(1, 10)
        ], 32, 32)
        self.enemies = [
            Enemy(path_groups[0][0], self.enemy_sprites),
            Enemy(path_groups[1][0], self.enemy_sprites),
            Enemy(path_groups[2][0], self.enemy_sprites)
        ]

        self.towers = []
        self.mortars = []
        self.crossbow_towers = []
        self.spawn_counter = 0
        self.score = 0
        self.money = 10000
        self.survival_time = 0
        self.last_score_time = 0
        self.spawn_frequency = 15000
        self.archer_spawn_frequency = 150 #4 * self.spawn_frequency
        self.giant_spawn_frequency = 1018 * self.spawn_frequency
        self.main_tower_position = next((x // grid_size, y // grid_size) for (x, y), color in map_data.items() if color == "green")
        self.main_tower = MainTower(self.main_tower_position)
        self.tower_placements = []


    def reset(self):
        self.__init__()  # Oyunu sıfırlamak için tüm değişkenleri yeniden başlat

    def spawn_enemy(self):
        if len(self.enemies) < 100:
            path_index = len(self.enemies) % len(path_groups)
            new_enemy = Enemy(path_groups[path_index][0], self.enemy_sprites)
            self.enemies.append(new_enemy)

    def spawn_archer(self):
        if len(self.enemies) < 100:
            path_index = len(self.enemies) % len(path_groups)
            new_archer = Archer(path_groups[path_index][0], self.archer_run_sprites, self.archer_attack_sprites)
            self.enemies.append(new_archer)

    def spawn_giant(self):
        if len(self.enemies) < 100:
            path_index = len(self.enemies) % len(path_groups)
            new_giant = Giant(path_groups[path_index][0])
            self.enemies.append(new_giant)

    def draw_hud(self, generation=None):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        money_text = font.render(f"Money: ${self.money}", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(money_text, (10, 50))
        if generation is not None:
            generation_text = font.render(f"Generation: {generation}", True, BLACK)
            screen.blit(generation_text, (10, 90))

    def update_score(self):
        if self.survival_time - self.last_score_time >= 5:
            self.score += 2
            self.last_score_time = self.survival_time
            print(f"Score increased: {self.score}, Survival Time: {self.survival_time}, Last Score Time: {self.last_score_time}")
            print(f"Enemies: {len(self.enemies)}, Towers: {len(self.towers)}, Mortars: {len(self.mortars)}")
            print(f"Crossbow Towers: {len(self.crossbow_towers)}, Main Tower Health: {self.main_tower.health}, Score: {self.score}, Money: ${self.money}\n")
    
    def play_game_instance(self):
        iteration = 0  # İterasyon sayacı
        while self.main_tower.health > 0:
            iteration += 1
            self.survival_time += 1 / fps  # Hayatta kalınan süreyi artır
            self.update_score()  # Skoru güncelle

            if iteration % (fps * 20) == 0:  # 20 saniyede bir debug mesajı
                print(f"Iteration: {iteration}, Enemies: {len(self.enemies)}, Towers: {len(self.towers)}, Mortars: {len(self.mortars)}")
                print(f"Crossbow Towers: {len(self.crossbow_towers)}, Main Tower Health: {self.main_tower.health}, Score: {self.score}, Money: ${self.money}\n")

            self.enemies = [enemy for enemy in self.enemies if enemy.health > 0]
            self.towers = [tower for tower in self.towers if tower.health > 0]
            self.mortars = [mortar for mortar in self.mortars if mortar.health > 0]
            self.crossbow_towers = [crossbow_tower for crossbow_tower in self.crossbow_towers if crossbow_tower.health > 0]

            self.spawn_counter += 1

            if self.spawn_counter % self.giant_spawn_frequency == 0:
                self.spawn_giant()
            elif self.spawn_counter % self.archer_spawn_frequency == 0:
                self.spawn_archer()
            elif self.spawn_counter % self.spawn_frequency == 0:
                self.spawn_enemy()

            self.main_tower.attack(self.enemies)
            for tower in self.towers:
                tower.attack(self.enemies)
            for mortar in self.mortars:
                mortar.update()
                mortar.attack(self.enemies)
            for crossbow_tower in self.crossbow_towers:
                crossbow_tower.attack(self.enemies)
            for enemy in self.enemies:
                enemy.move(self)

            screen.fill(WHITE)
            for path_group in path_groups:
                draw_paths(path_group)
            self.main_tower.draw()
            for tower in self.towers:
                tower.draw()
            for mortar in self.mortars:
                mortar.draw()
            for crossbow_tower in self.crossbow_towers:
                crossbow_tower.draw()
            for enemy in self.enemies:
                enemy.draw()

            self.draw_hud()
            pygame.display.update()
            clock.tick(fps)

class MainTower:
    def __init__(self, position):
        self.x, self.y = position  # Kule konumu (x, y)
        self.size = grid_size * 3  # Kule boyutu (3x3 grid)
        self.health = 1000  # Kule sağlığı
        self.max_health = 1000  # Maksimum sağlık
        self.damage_radius = 3 * grid_size + self.size / 2  # Saldırı yarıçapı (menzil)
        self.attack_power = 25  # Saldırı gücü
        self.cooldown = 0  # Saldırı bekleme süresi
        self.cooldown_max = 90  # Maksimum bekleme süresi

    def draw(self):
        tower_start_x = self.x * grid_size  # Kule başlangıç x konumu
        tower_start_y = self.y * grid_size  # Kule başlangıç y konumu
        rect = pygame.Rect(tower_start_x, tower_start_y, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, GREEN, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (tower_start_x, tower_start_y - 10), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def attack(self, enemies):
        if self.cooldown == 0:  # Bekleme süresi sıfırsa saldır
            tower_center_x = self.x * grid_size + self.size / 2  # Kule merkez x konumu
            tower_center_y = self.y * grid_size + self.size / 2  # Kule merkez y konumu

            for enemy in enemies:  # Düşmanları kontrol et
                if self.health > 0 and enemy.health > 0:  # Kule ve düşman sağlığı pozitif ise
                    enemy_center_x = enemy.x * grid_size + enemy.width / 2  # Düşman merkez x konumu
                    enemy_center_y = enemy.y * grid_size + enemy.height / 2  # Düşman merkez y konumu
                    distance = ((tower_center_x - enemy_center_x) ** 2 + (tower_center_y - enemy_center_y) ** 2) ** 0.5  # Kule ve düşman arasındaki mesafe
                    if distance <= self.damage_radius:  # Düşman menzil içindeyse
                        enemy.health -= self.attack_power  # Düşmana hasar ver
                        if enemy.health < 0:
                            enemy.health = 0  # Sağlık sıfırın altına düşerse sıfırla
                        self.cooldown = self.cooldown_max  # Saldırı sonrası bekleme süresini başlat
                        break  # İlk düşmana saldırdıktan sonra döngüden çık
        else:
            self.cooldown -= 1  # Bekleme süresini azalt


class Enemy:
    def __init__(self, path, sprites):
        self.path = path  # Düşmanın izleyeceği yol
        self.index = 0  # Yol üzerinde geçerli indeks
        self.x, self.y = self.path[self.index]  # Geçerli konum
        self.width = 32  # Düşmanın genişliği
        self.height = 32  # Düşmanın yüksekliği
        self.health = 60  # Düşmanın sağlığı
        self.max_health = 60  # Düşmanın maksimum sağlığı
        self.move_counter = 0  # Hareket sayacı
        self.move_frequency = 45  # Hareket frekansı
        self.attack_counter = 0  # Saldırı sayacı
        self.attack_frequency = 40  # Saldırı frekansı
        self.damage = 10  # Verilen hasar
        self.reward = 15  # Öldürüldüğünde verilen para miktarı
        self.score_value = 10  # Öldürüldüğünde verilen skor miktarı

        # Animasyon sprite'ları
        self.sprites = sprites[:8]  # Normal hareket animasyonları
        self.attack_sprites = sprites[8:]  # Saldırı animasyonları
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x * grid_size, self.y * grid_size)
        self.animation_speed = 0.15  # Animasyon hızını ayarla
        self.frame_counter = 0
        self.attacking = False
        self.direction = 'down'  # Başlangıç yönü

        self.target_x = self.x * grid_size
        self.target_y = self.y * grid_size

    def update(self):
        self.frame_counter += self.animation_speed
        if self.attacking:
            if self.frame_counter >= len(self.attack_sprites):
                self.frame_counter = 0
            self.current_sprite = int(self.frame_counter)
            self.image = self.attack_sprites[self.current_sprite]
        else:
            if self.frame_counter >= len(self.sprites):
                self.frame_counter = 0
            self.current_sprite = int(self.frame_counter)
            self.image = self.sprites[self.current_sprite]

        if self.direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)
        elif self.direction == 'up':
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.direction == 'down':
            self.image = pygame.transform.rotate(self.image, -90)

    def draw(self):
        # Sprite'ın konumunu path'e göre ayarla
        offset_x = (grid_size - self.width) // 2
        offset_y = grid_size - self.height
        screen.blit(self.image, (self.x * grid_size + offset_x, self.y * grid_size + offset_y))
        draw_health_bar(screen, (self.x * grid_size + offset_x, self.y * grid_size + offset_y - 20), self.health, self.max_health, self.width, 5)

    def move(self, game):
        if self.health > 0 and self.index < len(self.path) - 1:
            self.move_counter += 1
            if self.move_counter >= self.move_frequency:
                next_x, next_y = self.path[self.index + 1]
                if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                    self.index += 1
                    self.target_x = next_x * grid_size
                    self.target_y = next_y * grid_size
                    self.move_counter = 0

                    # Güncellenmiş konumu ve yönü ayarla
                    dx, dy = next_x - self.path[self.index - 1][0], next_y - self.path[self.index - 1][1]
                    if dx > 0:
                        self.direction = 'right'
                    elif dx < 0:
                        self.direction = 'left'
                    elif dy > 0:
                        self.direction = 'down'
                    elif dy < 0:
                        self.direction = 'up'

        # Hedef konuma doğru küçük adımlarla ilerle
        if self.x * grid_size < self.target_x:
            self.x += 1 / 10  # 10 adımda geç
        elif self.x * grid_size > self.target_x:
            self.x -= 1 / 10

        if self.y * grid_size < self.target_y:
            self.y += 1 / 10
        elif self.y * grid_size > self.target_y:
            self.y -= 1 / 10

        if self.health > 0 and self.index >= len(self.path) - 1:
            self.attack_counter += 1
            if self.attack_counter >= self.attack_frequency:
                game.main_tower.health -= self.damage  # Ana kuleye hasar ver
                if game.main_tower.health <= 0:
                    game.main_tower.health = 0
                    return
                self.attack_counter = 0
                self.attacking = True  # Saldırı animasyonunu başlat
        else:
            self.attacking = False

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)

    def is_in_attack_range(self, target):
        distance = ((self.x * grid_size - target.x * grid_size) ** 2 +
                    (self.y * grid_size - target.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
        return distance <= self.attack_range

    def attack(self, targets):
        for target in targets:
            if target.health > 0 and self.is_in_attack_range(target):
                target.health -= self.attack_power  # Hedefin sağlığını azalt
                if target.health <= 0:
                    target.health = 0  # Hedefin sağlığını sıfırla


                    

class Archer(Enemy):
    def __init__(self, path, run_sprites, attack_sprites):
        super().__init__(path, run_sprites + attack_sprites)
        self.attack_range = 4 * grid_size  # Saldırı menzili
        self.color = PURPLE  # Renk
        self.attack_power = 25  # Saldırı gücü
        self.health = 120  # Sağlık
        self.max_health = 120  # Maksimum sağlık
        self.attack_counter = 0  # Saldırı sayacı
        self.attack_frequency = 60  # Saldırı frekansı
        self.move_frequency = 60  # Hareket frekansı
        self.reward = 40  # Öldürüldüğünde verilen para miktarı
        self.score_value = 25  # Öldürüldüğünde verilen skor miktarı

        # Animasyon sprite'ları
        self.run_sprites = run_sprites
        self.attack_sprites = attack_sprites
        self.current_sprite = 0
        self.image = self.run_sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x * grid_size, self.y * grid_size)
        self.animation_speed = 10.0 / self.move_frequency  # 60 karede 10 frame (her frame 6 kare sürecek)
        self.frame_counter = 0
        self.attacking = False
        self.direction = 'down'  # Başlangıç yönü

        self.start_x = self.x * grid_size
        self.start_y = self.y * grid_size
        self.target_x = self.x * grid_size
        self.target_y = self.y * grid_size
        self.animation_steps = 10
        self.current_step = 0
        self.visual_x = self.x * grid_size
        self.visual_y = self.y * grid_size

    def update(self):
        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.run_sprites if not self.attacking else self.attack_sprites)
            self.image = (self.run_sprites if not self.attacking else self.attack_sprites)[self.current_sprite]

        if self.direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)
        elif self.direction == 'up':
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.direction == 'down':
            self.image = pygame.transform.rotate(self.image, -90)

    def draw(self):
        screen.blit(self.image, (self.visual_x, self.visual_y))
        draw_health_bar(screen, (self.visual_x, self.visual_y - 20), self.health, self.max_health, self.width, 5)

    def move(self, game):
        global score, money
        if self.health > 0 and self.index < len(self.path) - 1:
            target_hit = False
            combined_targets = game.towers + game.mortars + game.crossbow_towers + [game.main_tower]  # Tüm hedefler
            for target in combined_targets:
                if self.is_in_attack_range(target):
                    if self.attack_counter == 0:
                        self.attacking = True
                        self.attack([target])  # Hedefe saldır
                        if target.health <= 0:
                            target_hit = True
                        self.attack_counter = self.attack_frequency
                    break

            if target_hit:
                pass  # Hedef vurulduysa hareketsiz kal
            else:
                self.attacking = False
                if self.attack_counter == 0:
                    self.move_counter += 1
                    if self.move_counter >= self.move_frequency:
                        next_x, next_y = self.path[self.index + 1]
                        if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                            self.index += 1
                            self.start_x = self.visual_x
                            self.start_y = self.visual_y
                            self.target_x = next_x * grid_size
                            self.target_y = next_y * grid_size
                            self.current_step = 0
                            self.move_counter = 0

                            dx, dy = next_x - self.path[self.index - 1][0], next_y - self.path[self.index - 1][1]
                            if dx > 0:
                                self.direction = 'right'
                            elif dx < 0:
                                self.direction = 'left'
                            elif dy > 0:
                                self.direction = 'down'
                            elif dy < 0:
                                self.direction = 'up'

        # Adım adım görsel hareket
        step_x = (self.target_x - self.start_x) / self.animation_steps
        step_y = (self.target_y - self.start_y) / self.animation_steps

        if self.current_step < self.animation_steps:
            self.visual_x = self.start_x + step_x * self.current_step
            self.visual_y = self.start_y + step_y * self.current_step
            self.current_step += 1

        if self.attack_counter > 0:
            self.attack_counter -= 1

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)

    def is_in_attack_range(self, target):
        distance = ((self.x * grid_size - target.x * grid_size) ** 2 +
                    (self.y * grid_size - target.y * grid_size) ** 2) ** 0.5
        return distance <= self.attack_range

    def attack(self, targets):
        for target in targets:
            if target.health > 0 and self.is_in_attack_range(target):
                target.health -= self.attack_power
                if target.health <= 0:
                    target.health = 0  # Hedefin sağlığını sıfırla




"""


class Enemy:
    def __init__(self, path, sprites):
        self.path = path  # Düşmanın izleyeceği yol
        self.index = 0  # Yol üzerinde geçerli indeks
        self.x, self.y = self.path[self.index]  # Geçerli konum
        self.width = 32  # Düşmanın genişliği
        self.height = 32  # Düşmanın yüksekliği
        self.health = 60  # Düşmanın sağlığı
        self.max_health = 60  # Düşmanın maksimum sağlığı
        self.move_counter = 0  # Hareket sayacı
        self.move_frequency = 45  # Hareket frekansı
        self.attack_counter = 0  # Saldırı sayacı
        self.attack_frequency = 40  # Saldırı frekansı
        self.damage = 10  # Verilen hasar
        self.reward = 15  # Öldürüldüğünde verilen para miktarı
        self.score_value = 10  # Öldürüldüğünde verilen skor miktarı

        # Animasyon sprite'ları
        self.sprites = sprites[:8]  # Normal hareket animasyonları
        self.attack_sprites = sprites[8:]  # Saldırı animasyonları
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x * grid_size, self.y * grid_size)
        self.animation_speed = 0.15  # Animasyon hızını ayarla
        self.frame_counter = 0
        self.attacking = False
        self.direction = 'down'  # Başlangıç yönü

        self.target_x = self.x * grid_size
        self.target_y = self.y * grid_size

    def update(self):
        self.frame_counter += self.animation_speed
        if self.attacking:
            if self.frame_counter >= len(self.attack_sprites):
                self.frame_counter = 0
            self.current_sprite = int(self.frame_counter)
            self.image = self.attack_sprites[self.current_sprite]
        else:
            if self.frame_counter >= len(self.sprites):
                self.frame_counter = 0
            self.current_sprite = int(self.frame_counter)
            self.image = self.sprites[self.current_sprite]

        if self.direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)
        elif self.direction == 'up':
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.direction == 'down':
            self.image = pygame.transform.rotate(self.image, -90)

    def draw(self):
        # Sprite'ın konumunu path'e göre ayarla
        offset_x = (grid_size - self.width) // 2
        offset_y = grid_size - self.height
        screen.blit(self.image, (self.x * grid_size + offset_x, self.y * grid_size + offset_y))
        draw_health_bar(screen, (self.x * grid_size + offset_x, self.y * grid_size + offset_y - 20), self.health, self.max_health, self.width, 5)

    def move(self, game):
        if self.health > 0 and self.index < len(self.path) - 1:
            self.move_counter += 1
            if self.move_counter >= self.move_frequency:
                next_x, next_y = self.path[self.index + 1]
                if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                    self.index += 1
                    self.target_x = next_x * grid_size
                    self.target_y = next_y * grid_size
                    self.move_counter = 0

                    # Güncellenmiş konumu ve yönü ayarla
                    dx, dy = next_x - self.path[self.index - 1][0], next_y - self.path[self.index - 1][1]
                    if dx > 0:
                        self.direction = 'right'
                    elif dx < 0:
                        self.direction = 'left'
                    elif dy > 0:
                        self.direction = 'down'
                    elif dy < 0:
                        self.direction = 'up'

        # Hedef konuma doğru küçük adımlarla ilerle
        if self.x * grid_size < self.target_x:
            self.x += 1 / grid_size
        elif self.x * grid_size > self.target_x:
            self.x -= 1 / grid_size

        if self.y * grid_size < self.target_y:
            self.y += 1 / grid_size
        elif self.y * grid_size > self.target_y:
            self.y -= 1 / grid_size

        if self.health > 0 and self.index >= len(self.path) - 1:
            self.attack_counter += 1
            if self.attack_counter >= self.attack_frequency:
                game.main_tower.health -= self.damage
                if game.main_tower.health <= 0:
                    game.main_tower.health = 0
                    return
                self.attack_counter = 0
                self.attacking = True  # Saldırı animasyonunu başlat
        else:
            self.attacking = False

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)


class Archer(Enemy):
    def __init__(self, path, run_sprites, attack_sprites):
        super().__init__(path)
        self.attack_range = 4 * grid_size  # Saldırı menzili
        self.color = PURPLE  # Renk
        self.attack_power = 25  # Saldırı gücü
        self.health = 120  # Sağlık
        self.max_health = 120  # Maksimum sağlık
        self.attack_counter = 0  # Saldırı sayacı
        self.attack_frequency = 60  # Saldırı frekansı
        self.move_frequency = 60  # Hareket frekansı
        self.reward = 40  # Öldürüldüğünde verilen para miktarı
        self.score_value = 25  # Öldürüldüğünde verilen skor miktarı

        self.run_sprites = run_sprites
        self.attack_sprites = attack_sprites
        self.current_sprite = 0
        self.image = self.run_sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x * grid_size, self.y * grid_size)
        self.animation_speed = 0.15  # Animasyon hızını ayarla
        self.frame_counter = 0
        self.attacking = False
        self.direction = 'down'  # Başlangıç yönü

        self.target_x = self.x * grid_size
        self.target_y = self.y * grid_size

    def update(self):
        self.frame_counter += self.animation_speed
        if self.attacking:
            if self.frame_counter >= len(self.attack_sprites):
                self.frame_counter = 0
            self.current_sprite = int(self.frame_counter)
            self.image = self.attack_sprites[self.current_sprite]
        else:
            if self.frame_counter >= len(self.run_sprites):
                self.frame_counter = 0
            self.current_sprite = int(self.frame_counter)
            self.image = self.run_sprites[self.current_sprite]

        if self.direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)
        elif self.direction == 'up':
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.direction == 'down':
            self.image = pygame.transform.rotate(self.image, -90)

    def draw(self):
        # Sprite'ın konumunu path'e göre ayarla
        offset_x = (grid_size - self.width) // 2
        offset_y = grid_size - self.height
        screen.blit(self.image, (self.x * grid_size + offset_x, self.y * grid_size + offset_y))
        draw_health_bar(screen, (self.x * grid_size + offset_x, self.y * grid_size + offset_y - 20), self.health, self.max_health, self.width, 5)

    def move(self, game):
        global score, money
        if self.health > 0 and self.index < len(self.path) - 1:
            target_hit = False
            combined_targets = game.towers + game.mortars + game.crossbow_towers + [game.main_tower]  # Tüm hedefler
            for target in combined_targets:
                if self.is_in_attack_range(target):
                    if self.attack_counter == 0:
                        self.attack([target])  # Hedefe saldır
                        if target.health <= 0:
                            target_hit = True
                        self.attack_counter = self.attack_frequency
                    break

            if not target_hit:
                if self.attack_counter == 0:
                    self.move_counter += 1
                    if self.move_counter >= self.move_frequency // 10:  # Her frame'de hareket et
                        next_x, next_y = self.path[self.index + 1]
                        if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                            self.index += 1
                            self.target_x = next_x * grid_size
                            self.target_y = next_y * grid_size
                            self.move_counter = 0

                            # Güncellenmiş konumu ve yönü ayarla
                            dx, dy = next_x - self.path[self.index - 1][0], next_y - self.path[self.index - 1][1]
                            if dx > 0:
                                self.direction = 'right'
                            elif dx < 0:
                                self.direction = 'left'
                            elif dy > 0:
                                self.direction = 'down'
                            elif dy < 0:
                                self.direction = 'up'

        # Hedef konuma doğru küçük adımlarla ilerle
        if self.x * grid_size < self.target_x:
            self.x += 1 / 10  # 10 adımda geç
        elif self.x * grid_size > self.target_x:
            self.x -= 1 / 10

        if self.y * grid_size < self.target_y:
            self.y += 1 / 10
        elif self.y * grid_size > self.target_y:
            self.y -= 1 / 10

        if self.health > 0 and self.index >= len(self.path) - 1:
            self.attack_counter += 1
            if self.attack_counter >= self.attack_frequency:
                game.main_tower.health -= self.damage  # Ana kuleye hasar ver
                if game.main_tower.health <= 0:
                    game.main_tower.health = 0
                    return
                self.attack_counter = 0
                self.attacking = True  # Saldırı animasyonunu başlat
        else:
            self.attacking = False

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)

    def is_in_attack_range(self, target):
        distance = ((self.x * grid_size - target.x * grid_size) ** 2 +
                    (self.y * grid_size - target.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
        return distance <= self.attack_range

    def attack(self, targets):
        for target in targets:
            if target.health > 0 and self.is_in_attack_range(target):
                target.health -= self.attack_power  # Hedefin sağlığını azalt
                if target.health <= 0:
                    target.health = 0  # Hedefin sağlığını sıfırla

                    
"""

class Giant(Enemy):
    def __init__(self, path):
        super().__init__(path)
        self.attack_range = 1 * grid_size  # Saldırı menzili
        self.color = ORANGE  # Renk
        self.attack_power = 75  # Saldırı gücü
        self.health = 400  # Sağlık
        self.max_health = 400  # Maksimum sağlık
        self.move_frequency = 75  # Hareket frekansı
        self.attack_frequency = 120  # Saldırı frekansı
        self.reward = 80  # Öldürüldüğünde verilen para miktarı
        self.score_value = 60  # Öldürüldüğünde verilen skor miktarı

    def draw(self):
        if self.health > 0:
            rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.width, self.height)  # Dikdörtgeni tanımla
            pygame.draw.rect(screen, self.color, rect)  # Ekrana çiz
            draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.width, 5)  # Sağlık barını çiz

    def move(self, game):
        if self.health > 0:
            if self.index < len(self.path) - 1:
                target_hit = False
                combined_targets = game.towers + game.mortars + game.crossbow_towers  # Tüm hedefler

                # Hedef menzilde mi kontrol et
                for target in combined_targets:
                    if self.is_in_attack_range(target):
                        if self.attack_counter == 0:
                            self.attack([target])  # Hedefe saldır
                            if target.health <= 0:
                                target_hit = True
                            self.attack_counter = self.attack_frequency
                        break

                # Hedef menzilde değilse hareket et
                if not target_hit:
                    if self.attack_counter == 0:
                        self.move_counter += 1
                        if self.move_counter >= self.move_frequency:
                            next_x, next_y = self.path[self.index + 1]
                            if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                                self.index += 1
                                self.x, self.y = next_x, next_y  # Konumu güncelle
                                self.move_counter = 0

            # Saldırı süresini azalt
            if self.attack_counter > 0:
                self.attack_counter -= 1

            # Ana kuleye saldırı
            if self.index >= len(self.path) - 1:
                if self.attack_counter == 0:
                    game.main_tower.health -= self.attack_power  # Ana kuleye hasar ver
                    if game.main_tower.health <= 0:
                        game.main_tower.health = 0
                        return
                    self.attack_counter = self.attack_frequency

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)

    def is_in_attack_range(self, target):
        # Hedefin menzilde olup olmadığını kontrol et
        distance = ((self.x * grid_size - target.x * grid_size) ** 2 +
                    (self.y * grid_size - target.y * grid_size) ** 2) ** 0.5
        return distance <= self.attack_range

    def attack(self, targets):
        # Hedeflere saldır
        for target in targets:
            if target.health > 0 and self.is_in_attack_range(target):
                target.health -= self.attack_power  # Hedefin sağlığını azalt
                if target.health <= 0:
                    target.health = 0  # Hedefin sağlığını sıfırla

class Tower:
    def __init__(self, x, y):
        self.x = x  # Kule konumu x
        self.y = y  # Kule konumu y
        self.size = grid_size  # Kule boyutu
        self.health = 200  # Kule sağlığı
        self.max_health = 200  # Maksimum sağlık
        self.damage = 25  # Kule hasarı
        self.attack_range = 4 * grid_size  # Saldırı menzili
        self.attack_cooldown = 60  # Saldırı bekleme süresi
        self.cost = 50  # Kule maliyeti
        self.total_damage_dealt = 0  # Toplam verilen hasar

    def draw(self):
        rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, BLUE, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def attack(self, enemies):
        if self.attack_cooldown == 0:
            for enemy in enemies:
                if enemy.health > 0:
                    distance = ((self.x * grid_size - enemy.x * grid_size) ** 2 +
                                (self.y * grid_size - enemy.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
                    if distance <= self.attack_range:
                        enemy.health -= self.damage  # Hedefin sağlığını azalt
                        self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                        if enemy.health <= 0:
                            enemy.health = 0  # Hedefin sağlığını sıfırla
                        self.attack_cooldown = 60  # Saldırı bekleme süresini sıfırla
                        break  # İlk hedefe saldırdıktan sonra döngüden çık
        else:
            self.attack_cooldown -= 1  # Saldırı bekleme süresini azalt

class CrossbowTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.damage = 3  # Hasar değeri
        self.attack_range = 2 * grid_size  # Saldırı menzili
        self.attack_cooldown = 15  # Saldırı bekleme süresi
        self.color = LIGHT_BLUE  # Renk
        self.cost = 25  # Arbalet kulesi maliyeti
        self.health = 80  # Sağlık
        self.max_health = 80  # Maksimum sağlık

    def draw(self):
        rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, self.color, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def attack(self, enemies):
        if self.attack_cooldown == 0:  # Bekleme süresi sıfırsa saldır
            for enemy in enemies:  # Düşmanları kontrol et
                if enemy.health > 0:  # Düşman sağlığı pozitif ise
                    distance = ((self.x * grid_size - enemy.x * grid_size) ** 2 +
                                (self.y * grid_size - enemy.y * grid_size) ** 2) ** 0.5  # Kule ve düşman arasındaki mesafe
                    if distance <= self.attack_range:  # Düşman menzil içindeyse
                        enemy.health -= self.damage  # Düşmana hasar ver
                        self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                        if enemy.health <= 0:
                            enemy.health = 0  # Sağlık sıfırın altına düşerse sıfırla
                        self.attack_cooldown = 10  # Saldırı sonrası bekleme süresini başlat
                        break  # İlk düşmana saldırdıktan sonra döngüden çık
        else:
            self.attack_cooldown -= 1  # Bekleme süresini azalt

class Mortar(Tower):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 400  # Sağlık
        self.max_health = 400  # Maksimum sağlık
        self.damage = 50  # Hasar değeri
        self.attack_range = 7 * grid_size  # Saldırı menzili
        self.attack_cooldown = 240  # Saldırı bekleme süresi
        self.self_damage = 2  # Kendi kendine zarar verme miktarı
        self.color = DARK_BLUE  # Renk
        self.self_damage_cooldown = 9  # Kendi kendine zarar verme bekleme süresi
        self.cost = 120  # Havan maliyeti

    def draw(self):
        rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, self.color, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def update(self):
        if self.self_damage_cooldown == 0:
            self.health -= self.self_damage  # Kendi kendine zarar ver
            if self.health < 0:
                self.health = 0  # Sağlığı sıfırla
            self.self_damage_cooldown = 9  # Kendi kendine zarar verme bekleme süresini sıfırla
        else:
            self.self_damage_cooldown -= 1  # Kendi kendine zarar verme bekleme süresini azalt

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1  # Saldırı bekleme süresini azalt

    def attack(self, enemies):
        if self.attack_cooldown == 0:
            for enemy in enemies:
                if enemy.health > 0:
                    distance = ((self.x * grid_size - enemy.x * grid_size) ** 2 +
                                (self.y * grid_size - enemy.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
                    if distance <= self.attack_range:
                        # Hedefin kendisine zarar ver
                        enemy.health -= self.damage
                        self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                        if enemy.health <= 0:
                            enemy.health = 0  # Hedefin sağlığını sıfırla
                        
                        # 2x2 alana saldırı
                        for dx in range(-1, 2):
                            for dy in range(-1, 2):
                                if dx != 0 or dy != 0:  # Mevcut pozisyon dışında
                                    target_x, target_y = enemy.x + dx, enemy.y + dy
                                    for e in enemies:
                                        if e.x == target_x and e.y == target_y and e.health > 0:
                                            e.health -= self.damage  # Hedefin sağlığını azalt
                                            self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                                            if e.health <= 0:
                                                e.health = 0  # Hedefin sağlığını sıfırla
                        self.attack_cooldown = 240  # Saldırı bekleme süresini sıfırla
                        break  # İlk hedefe saldırdıktan sonra döngüden çık
        else:
            self.attack_cooldown -= 1  # Saldırı bekleme süresini azalt


"""

# Pygame başlatma ve ekran ayarları
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))

# Renk tanımları
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
DARK_BLUE = (0, 0, 139)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
TEAL = (0, 128, 128)
BLACK = (0, 0, 0)

# Zaman ve FPS ayarları
clock = pygame.time.Clock()
fps = 60

# Grid ayarları
grid_size = 20
grid_width = screen_width // grid_size
grid_height = screen_height // grid_size

def draw_health_bar(screen, position, health, max_health, width, height):
    pygame.draw.rect(screen, (128, 128, 128), (position[0], position[1] - 10, width, height))
    current_health_width = (health / max_health) * width
    pygame.draw.rect(screen, ORANGE, (position[0], position[1] - 10, current_health_width, height))

def load_map_data(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return {(int(item[0]), int(item[1])): item[2] for item in data}

def find_path_starts_and_ends(grid_data):
    path_starts = {}
    path_ends = {}
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for (x, y), color in grid_data.items():
        if color == "grey":
            neighbors = [(x + dx, y + dy) for dx, dy in directions]
            neighbor_colors = [grid_data.get((x + dx, y + dy), "white") for dx, dy in directions]
            if neighbor_colors.count("grey") == 1 and neighbor_colors.count("white") == 3:
                path_starts[(x, y)] = True
            if neighbor_colors.count("grey") == 1 and neighbor_colors.count("green") == 1 and neighbor_colors.count("white") == 2:
                path_ends[(x, y)] = True

    return path_starts, path_ends

def find_paths(grid_data, path_starts):
    visited = set()
    paths = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def dfs(start):
        stack = [start]
        path = []
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                path.append(current)
                for dx, dy in directions:
                    neighbor = (current[0] + dx, current[1] + dy)
                    if grid_data.get(neighbor, None) == 'grey' and neighbor not in visited:
                        stack.append(neighbor)
        return path

    for start in path_starts:
        if start not in visited:
            path = dfs(start)
            if path:
                paths.append(path)

    return paths

map_data = load_map_data("map.json")
grid_data = {(x // grid_size, y // grid_size): color for (x, y), color in map_data.items()}
path_starts, path_ends = find_path_starts_and_ends(grid_data)
paths = find_paths(grid_data, path_starts)
path_groups = [paths[i::3] for i in range(3)]

def draw_paths(paths):
    for path in paths:
        for x, y in path:
            rect = pygame.Rect(x * grid_size, y * grid_size, grid_size, grid_size)
            pygame.draw.rect(screen, GRAY, rect)

class Game:
    def __init__(self):
        self.enemies = [
            Enemy(path_groups[0][0]),
            Archer(path_groups[1][0]),
            Enemy(path_groups[2][0])
        ]
        self.towers = []
        self.mortars = []
        self.crossbow_towers = []
        self.spawn_counter = 0
        self.score = 0
        self.money = 100  # Oyuncunun başlangıç parası
        self.survival_time = 0  # Hayatta kalınan süre
        self.last_score_time = 0  # Son skor ekleme zamanı
        self.spawn_frequency = 150  # Her 2.5 saniyede bir spawn kontrolü
        self.archer_spawn_frequency = 4 * self.spawn_frequency  # Her 4 döngüde bir okçu doğurma
        self.giant_spawn_frequency = 8 * self.spawn_frequency  # Her 8 döngüde bir dev doğurma
        self.main_tower_position = next((x // grid_size, y // grid_size) for (x, y), color in map_data.items() if color == "green")
        self.main_tower = MainTower(self.main_tower_position)
        self.tower_placements = []  # Yeni eklenen liste

    def reset(self):
        self.__init__()  # Oyunu sıfırlamak için tüm değişkenleri yeniden başlat

    def spawn_enemy(self):
        if len(self.enemies) < 100:
            path_index = len(self.enemies) % len(path_groups)
            new_enemy = Enemy(path_groups[path_index][0])
            self.enemies.append(new_enemy)

    def spawn_archer(self):
        if len(self.enemies) < 100:
            path_index = len(self.enemies) % len(path_groups)
            new_archer = Archer(path_groups[path_index][0])
            self.enemies.append(new_archer)

    def spawn_giant(self):
        if len(self.enemies) < 100:
            path_index = len(self.enemies) % len(path_groups)
            new_giant = Giant(path_groups[path_index][0])
            self.enemies.append(new_giant)

    def draw_hud(self, generation=None):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        money_text = font.render(f"Money: ${self.money}", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(money_text, (10, 50))
        if generation is not None:
            generation_text = font.render(f"Generation: {generation}", True, BLACK)
            screen.blit(generation_text, (10, 90))

    def update_score(self):
        if self.survival_time - self.last_score_time >= 5:
            self.score += 2
            self.last_score_time = self.survival_time
            print(f"Score increased: {self.score}, Survival Time: {self.survival_time}, Last Score Time: {self.last_score_time}")
            print(f"Enemies: {len(self.enemies)}, Towers: {len(self.towers)}, Mortars: {len(self.mortars)}")
            print(f"Crossbow Towers: {len(self.crossbow_towers)}, Main Tower Health: {self.main_tower.health}, Score: {self.score}, Money: ${self.money}\n")
    
    def play_game_instance(self):
        iteration = 0  # İterasyon sayacı
        while self.main_tower.health > 0:
            iteration += 1
            self.survival_time += 1 / fps  # Hayatta kalınan süreyi artır
            self.update_score()  # Skoru güncelle

            if iteration % (fps * 20) == 0:  # 20 saniyede bir debug mesajı
                print(f"Iteration: {iteration}, Enemies: {len(self.enemies)}, Towers: {len(self.towers)}, Mortars: {len(self.mortars)}")
                print(f"Crossbow Towers: {len(self.crossbow_towers)}, Main Tower Health: {self.main_tower.health}, Score: {self.score}, Money: ${self.money}\n")

            self.enemies = [enemy for enemy in self.enemies if enemy.health > 0]
            self.towers = [tower for tower in self.towers if tower.health > 0]
            self.mortars = [mortar for mortar in self.mortars if mortar.health > 0]
            self.crossbow_towers = [crossbow_tower for crossbow_tower in self.crossbow_towers if crossbow_tower.health > 0]

            self.spawn_counter += 1

            if self.spawn_counter % self.giant_spawn_frequency == 0:
                self.spawn_giant()
            elif self.spawn_counter % self.archer_spawn_frequency == 0:
                self.spawn_archer()
            elif self.spawn_counter % self.spawn_frequency == 0:
                self.spawn_enemy()

            self.main_tower.attack(self.enemies)
            for tower in self.towers:
                tower.attack(self.enemies)
            for mortar in self.mortars:
                mortar.update()
                mortar.attack(self.enemies)
            for crossbow_tower in self.crossbow_towers:
                crossbow_tower.attack(self.enemies)
            for enemy in self.enemies:
                enemy.move(self)

            screen.fill(WHITE)
            for path_group in path_groups:
                draw_paths(path_group)
            self.main_tower.draw()
            for tower in self.towers:
                tower.draw()
            for mortar in self.mortars:
                mortar.draw()
            for crossbow_tower in self.crossbow_towers:
                crossbow_tower.draw()
            for enemy in self.enemies:
                enemy.draw()

            self.draw_hud()
            pygame.display.update()
            clock.tick(fps)

class MainTower:
    def __init__(self, position):
        self.x, self.y = position  # Kule konumu (x, y)
        self.size = grid_size * 3  # Kule boyutu (3x3 grid)
        self.health = 1000  # Kule sağlığı
        self.max_health = 1000  # Maksimum sağlık
        self.damage_radius = 3 * grid_size + self.size / 2  # Saldırı yarıçapı (menzil)
        self.attack_power = 25  # Saldırı gücü
        self.cooldown = 0  # Saldırı bekleme süresi
        self.cooldown_max = 90  # Maksimum bekleme süresi

    def draw(self):
        tower_start_x = self.x * grid_size  # Kule başlangıç x konumu
        tower_start_y = self.y * grid_size  # Kule başlangıç y konumu
        rect = pygame.Rect(tower_start_x, tower_start_y, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, GREEN, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (tower_start_x, tower_start_y - 10), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def attack(self, enemies):
        if self.cooldown == 0:  # Bekleme süresi sıfırsa saldır
            tower_center_x = self.x * grid_size + self.size / 2  # Kule merkez x konumu
            tower_center_y = self.y * grid_size + self.size / 2  # Kule merkez y konumu

            for enemy in enemies:  # Düşmanları kontrol et
                if self.health > 0 and enemy.health > 0:  # Kule ve düşman sağlığı pozitif ise
                    enemy_center_x = enemy.x * grid_size + enemy.width / 2  # Düşman merkez x konumu
                    enemy_center_y = enemy.y * grid_size + enemy.height / 2  # Düşman merkez y konumu
                    distance = ((tower_center_x - enemy_center_x) ** 2 + (tower_center_y - enemy_center_y) ** 2) ** 0.5  # Kule ve düşman arasındaki mesafe
                    if distance <= self.damage_radius:  # Düşman menzil içindeyse
                        enemy.health -= self.attack_power  # Düşmana hasar ver
                        if enemy.health < 0:
                            enemy.health = 0  # Sağlık sıfırın altına düşerse sıfırla
                        self.cooldown = self.cooldown_max  # Saldırı sonrası bekleme süresini başlat
                        break  # İlk düşmana saldırdıktan sonra döngüden çık
        else:
            self.cooldown -= 1  # Bekleme süresini azalt

class Enemy:
    def __init__(self, path):
        self.path = path  # Düşmanın izleyeceği yol
        self.index = 0  # Yol üzerinde geçerli indeks
        self.x, self.y = self.path[self.index]  # Geçerli konum
        self.width = grid_size  # Düşmanın genişliği
        self.height = grid_size  # Düşmanın yüksekliği
        self.health = 60  # Düşmanın sağlığı
        self.max_health = 60  # Düşmanın maksimum sağlığı
        self.move_counter = 0  # Hareket sayacı
        self.move_frequency = 45  # Hareket frekansı
        self.attack_counter = 0  # Saldırı sayacı
        self.attack_frequency = 40  # Saldırı frekansı
        self.damage = 10  # Verilen hasar
        self.color = RED  # Düşmanın rengi
        self.reward = 15  # Öldürüldüğünde verilen para miktarı
        self.score_value = 10  # Öldürüldüğünde verilen skor miktarı

    def draw(self):
        if self.health > 0:
            rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.width, self.height)  # Düşmanın dikdörtgeni
            pygame.draw.rect(screen, self.color, rect)  # Düşmanı ekrana çiz
            draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.width, 5)  # Sağlık barını çiz

    def move(self, game):
        if self.health > 0 and self.index < len(self.path) - 1:
            self.move_counter += 1
            if self.move_counter >= self.move_frequency:
                next_x, next_y = self.path[self.index + 1]
                if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                    self.index += 1
                    self.x, self.y = next_x, next_y  # Konumu güncelle
                    self.move_counter = 0

        if self.health > 0 and self.index >= len(self.path) - 1:
            self.attack_counter += 1
            if self.attack_counter >= self.attack_frequency:
                game.main_tower.health -= self.damage  # Ana kuleye hasar ver
                if game.main_tower.health <= 0:
                    game.main_tower.health = 0
                    return
                self.attack_counter = 0

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)

class Archer(Enemy):
    def __init__(self, path):
        super().__init__(path)
        self.attack_range = 4 * grid_size  # Saldırı menzili
        self.color = PURPLE  # Renk
        self.attack_power = 25  # Saldırı gücü
        self.health = 120  # Sağlık
        self.max_health = 120  # Maksimum sağlık
        self.attack_counter = 0  # Saldırı sayacı
        self.attack_frequency = 60  # Saldırı frekansı
        self.move_frequency = 60  # Hareket frekansı
        self.reward = 40  # Öldürüldüğünde verilen para miktarı
        self.score_value = 25  # Öldürüldüğünde verilen skor miktarı

    def move(self, game):
        global score, money
        if self.health > 0 and self.index < len(self.path) - 1:
            target_hit = False
            combined_targets = game.towers + game.mortars + game.crossbow_towers + [game.main_tower]  # Tüm hedefler
            for target in combined_targets:
                if self.is_in_attack_range(target):
                    if self.attack_counter == 0:
                        self.attack([target])  # Hedefe saldır
                        if target.health <= 0:
                            target_hit = True
                        self.attack_counter = self.attack_frequency
                    break

            if target_hit:
                pass  # Hedef vurulduysa hareketsiz kal
            else:
                if self.attack_counter == 0:
                    self.move_counter += 1
                    if self.move_counter >= self.move_frequency:
                        next_x, next_y = self.path[self.index + 1]
                        if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                            self.index += 1
                            self.x, self.y = next_x, next_y  # Konumu güncelle
                            self.move_counter = 0
        if self.attack_counter > 0:
            self.attack_counter -= 1  # Saldırı süresini azalt

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)



    def is_in_attack_range(self, target):
        distance = ((self.x * grid_size - target.x * grid_size) ** 2 +
                    (self.y * grid_size - target.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
        return distance <= self.attack_range
    
    def attack(self, targets):
        for target in targets:
            if target.health > 0 and self.is_in_attack_range(target):
                target.health -= self.attack_power  # Hedefin sağlığını azalt
                if target.health <= 0:
                    target.health = 0  # Hedefin sağlığını sıfırla

class Giant(Enemy):
    def __init__(self, path):
        super().__init__(path)
        self.attack_range = 1 * grid_size  # Saldırı menzili
        self.color = ORANGE  # Renk
        self.attack_power = 75  # Saldırı gücü
        self.health = 400  # Sağlık
        self.max_health = 400  # Maksimum sağlık
        self.move_frequency = 75  # Hareket frekansı
        self.attack_frequency = 120  # Saldırı frekansı
        self.reward = 80  # Öldürüldüğünde verilen para miktarı
        self.score_value = 60  # Öldürüldüğünde verilen skor miktarı

    def draw(self):
        if self.health > 0:
            rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.width, self.height)  # Dikdörtgeni tanımla
            pygame.draw.rect(screen, self.color, rect)  # Ekrana çiz
            draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.width, 5)  # Sağlık barını çiz

    def move(self, game):
        if self.health > 0:
            if self.index < len(self.path) - 1:
                target_hit = False
                combined_targets = game.towers + game.mortars + game.crossbow_towers  # Tüm hedefler

                # Hedef menzilde mi kontrol et
                for target in combined_targets:
                    if self.is_in_attack_range(target):
                        if self.attack_counter == 0:
                            self.attack([target])  # Hedefe saldır
                            if target.health <= 0:
                                target_hit = True
                            self.attack_counter = self.attack_frequency
                        break

                # Hedef menzilde değilse hareket et
                if not target_hit:
                    if self.attack_counter == 0:
                        self.move_counter += 1
                        if self.move_counter >= self.move_frequency:
                            next_x, next_y = self.path[self.index + 1]
                            if not any(enemy.x == next_x and enemy.y == next_y for enemy in game.enemies if enemy is not self):
                                self.index += 1
                                self.x, self.y = next_x, next_y  # Konumu güncelle
                                self.move_counter = 0

            # Saldırı süresini azalt
            if self.attack_counter > 0:
                self.attack_counter -= 1

            # Ana kuleye saldırı
            if self.index >= len(self.path) - 1:
                if self.attack_counter == 0:
                    game.main_tower.health -= self.attack_power  # Ana kuleye hasar ver
                    if game.main_tower.health <= 0:
                        game.main_tower.health = 0
                        return
                    self.attack_counter = self.attack_frequency

        if self.health <= 0:
            game.score += self.score_value
            game.money += self.reward
            game.enemies.remove(self)

    def is_in_attack_range(self, target):
        # Hedefin menzilde olup olmadığını kontrol et
        distance = ((self.x * grid_size - target.x * grid_size) ** 2 +
                    (self.y * grid_size - target.y * grid_size) ** 2) ** 0.5
        return distance <= self.attack_range

    def attack(self, targets):
        # Hedeflere saldır
        for target in targets:
            if target.health > 0 and self.is_in_attack_range(target):
                target.health -= self.attack_power  # Hedefin sağlığını azalt
                if target.health <= 0:
                    target.health = 0  # Hedefin sağlığını sıfırla

class Tower:
    def __init__(self, x, y):
        self.x = x  # Kule konumu x
        self.y = y  # Kule konumu y
        self.size = grid_size  # Kule boyutu
        self.health = 200  # Kule sağlığı
        self.max_health = 200  # Maksimum sağlık
        self.damage = 25  # Kule hasarı
        self.attack_range = 4 * grid_size  # Saldırı menzili
        self.attack_cooldown = 60  # Saldırı bekleme süresi
        self.cost = 50  # Kule maliyeti
        self.total_damage_dealt = 0  # Toplam verilen hasar

    def draw(self):
        rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, BLUE, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def attack(self, enemies):
        if self.attack_cooldown == 0:
            for enemy in enemies:
                if enemy.health > 0:
                    distance = ((self.x * grid_size - enemy.x * grid_size) ** 2 +
                                (self.y * grid_size - enemy.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
                    if distance <= self.attack_range:
                        enemy.health -= self.damage  # Hedefin sağlığını azalt
                        self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                        if enemy.health <= 0:
                            enemy.health = 0  # Hedefin sağlığını sıfırla
                        self.attack_cooldown = 60  # Saldırı bekleme süresini sıfırla
                        break  # İlk hedefe saldırdıktan sonra döngüden çık
        else:
            self.attack_cooldown -= 1  # Saldırı bekleme süresini azalt

class CrossbowTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.damage = 3  # Hasar değeri
        self.attack_range = 2 * grid_size  # Saldırı menzili
        self.attack_cooldown = 15  # Saldırı bekleme süresi
        self.color = LIGHT_BLUE  # Renk
        self.cost = 25  # Arbalet kulesi maliyeti
        self.health = 80  # Sağlık
        self.max_health = 80  # Maksimum sağlık

    def draw(self):
        rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, self.color, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def attack(self, enemies):
        if self.attack_cooldown == 0:  # Bekleme süresi sıfırsa saldır
            for enemy in enemies:  # Düşmanları kontrol et
                if enemy.health > 0:  # Düşman sağlığı pozitif ise
                    distance = ((self.x * grid_size - enemy.x * grid_size) ** 2 +
                                (self.y * grid_size - enemy.y * grid_size) ** 2) ** 0.5  # Kule ve düşman arasındaki mesafe
                    if distance <= self.attack_range:  # Düşman menzil içindeyse
                        enemy.health -= self.damage  # Düşmana hasar ver
                        self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                        if enemy.health <= 0:
                            enemy.health = 0  # Sağlık sıfırın altına düşerse sıfırla
                        self.attack_cooldown = 10  # Saldırı sonrası bekleme süresini başlat
                        break  # İlk düşmana saldırdıktan sonra döngüden çık
        else:
            self.attack_cooldown -= 1  # Bekleme süresini azalt

class Mortar(Tower):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 400  # Sağlık
        self.max_health = 400  # Maksimum sağlık
        self.damage = 50  # Hasar değeri
        self.attack_range = 7 * grid_size  # Saldırı menzili
        self.attack_cooldown = 240  # Saldırı bekleme süresi
        self.self_damage = 2  # Kendi kendine zarar verme miktarı
        self.color = DARK_BLUE  # Renk
        self.self_damage_cooldown = 9  # Kendi kendine zarar verme bekleme süresi
        self.cost = 120  # Havan maliyeti

    def draw(self):
        rect = pygame.Rect(self.x * grid_size, self.y * grid_size, self.size, self.size)  # Kule dikdörtgeni
        pygame.draw.rect(screen, self.color, rect)  # Kuleyi ekrana çiz
        draw_health_bar(screen, (self.x * grid_size, self.y * grid_size - 20), self.health, self.max_health, self.size, 5)  # Sağlık barını çiz

    def update(self):
        if self.self_damage_cooldown == 0:
            self.health -= self.self_damage  # Kendi kendine zarar ver
            if self.health < 0:
                self.health = 0  # Sağlığı sıfırla
            self.self_damage_cooldown = 9  # Kendi kendine zarar verme bekleme süresini sıfırla
        else:
            self.self_damage_cooldown -= 1  # Kendi kendine zarar verme bekleme süresini azalt

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1  # Saldırı bekleme süresini azalt

    def attack(self, enemies):
        if self.attack_cooldown == 0:
            for enemy in enemies:
                if enemy.health > 0:
                    distance = ((self.x * grid_size - enemy.x * grid_size) ** 2 +
                                (self.y * grid_size - enemy.y * grid_size) ** 2) ** 0.5  # Hedefe olan mesafeyi hesapla
                    if distance <= self.attack_range:
                        # Hedefin kendisine zarar ver
                        enemy.health -= self.damage
                        self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                        if enemy.health <= 0:
                            enemy.health = 0  # Hedefin sağlığını sıfırla
                        
                        # 2x2 alana saldırı
                        for dx in range(-1, 2):
                            for dy in range(-1, 2):
                                if dx != 0 or dy != 0:  # Mevcut pozisyon dışında
                                    target_x, target_y = enemy.x + dx, enemy.y + dy
                                    for e in enemies:
                                        if e.x == target_x and e.y == target_y and e.health > 0:
                                            e.health -= self.damage  # Hedefin sağlığını azalt
                                            self.total_damage_dealt += self.damage  # Toplam verilen hasarı güncelle
                                            if e.health <= 0:
                                                e.health = 0  # Hedefin sağlığını sıfırla
                        self.attack_cooldown = 240  # Saldırı bekleme süresini sıfırla
                        break  # İlk hedefe saldırdıktan sonra döngüden çık
        else:
            self.attack_cooldown -= 1  # Saldırı bekleme süresini azalt

       