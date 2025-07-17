import pygame
import random
import sys
import math
from pygame import gfxdrawio
import aiogram
from aiogram import pygame

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Супер-Ловец фруктов (хардкор)")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)
BLUE = (50, 50, 255)
PURPLE = (200, 50, 255)
ORANGE = (255, 150, 50)

# Игрок (корзина)
player_width = 100
player_height = 20
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - 50
player_speed = 10
player_invincible = False  # Неуязвимость

# Временные бонусы
bonuses = {
    "speed": {"active": False, "timer": 0, "duration": 300},  # 5 сек (60 FPS * 5)
    "invincible": {"active": False, "timer": 0, "duration": 300},
    "double_points": {"active": False, "timer": 0, "duration": 300}
}

# Фрукты, бомбы и бонусы
class GameObject:
    def __init__(self, obj_type):
        self.type = obj_type
        self.radius = 15
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = -self.radius
        self.speed = random.randint(3, 8)
        
        # Цвета и свойства
        if self.type == "apple":
            self.color = RED
            self.points = 1
        elif self.type == "banana":
            self.color = YELLOW
            self.points = 2
        elif self.type == "bomb":
            self.color = BLACK
            self.damage = 1
        elif self.type == "slow_bomb":
            self.color = PURPLE
            self.damage = 0  # Не вредит, но замедляет
        elif self.type == "mine":
            self.color = ORANGE
            self.damage = 2  # Двойной урон!
        elif self.type == "bonus_speed":
            self.color = GREEN
        elif self.type == "bonus_invincible":
            self.color = BLUE
        elif self.type == "bonus_double":
            self.color = WHITE
    
    def draw(self):
        if self.type in ["bomb", "slow_bomb", "mine"]:
            gfxdraw.aacircle(screen, int(self.x), int(self.y), self.radius, self.color)
            gfxdraw.filled_circle(screen, int(self.x), int(self.y), self.radius, self.color)
            # Фитиль для бомб
            pygame.draw.line(screen, RED, (self.x - 5, self.y - 10), (self.x + 5, self.y - 10), 2)
        else:
            gfxdraw.aacircle(screen, int(self.x), int(self.y), self.radius, self.color)
            gfxdraw.filled_circle(screen, int(self.x), int(self.y), self.radius, self.color)

objects = []
spawn_timer = 0
spawn_delay = 45  # Чем меньше, тем чаще спавн

# Игровые переменные
score = 0
combo = 0
max_combo = 0
lives = 3
level = 1
font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_small = pygame.font.SysFont("Arial", 24)
game_over = False
clock = pygame.time.Clock()

# Частицы для анимаций
particles = []

def spawn_object():
    """Спавнит фрукты, бомбы или бонусы с умным распределением."""
    choices = ["apple"] * 5 + ["banana"] * 3 + ["bomb"] * 2
    if level >= 2:
        choices += ["slow_bomb"] * 1
    if level >= 3:
        choices += ["mine"] * 1
    if level >= 4 and random.random() < 0.1:
        choices += ["bonus_speed", "bonus_invincible", "bonus_double"]
    
    obj_type = random.choice(choices)
    objects.append(GameObject(obj_type))

def check_collision(obj):
    """Проверяет столкновение с корзиной."""
    return (obj.y + obj.radius >= player_y and
            obj.x >= player_x - obj.radius and
            obj.x <= player_x + player_width + obj.radius)

def create_particles(x, y, color, count=10):
    """Создаёт частицы для анимации."""
    for _ in range(count):
        particles.append({
            "x": x,
            "y": y,
            "color": color,
            "speed": random.uniform(1, 3),
            "angle": random.uniform(0, math.pi * 2),
            "life": 30
        })

def update_particles():
    """Обновляет и рисует частицы."""
    for p in particles[:]:
        p["x"] += math.cos(p["angle"]) * p["speed"]
        p["y"] += math.sin(p["angle"]) * p["speed"]
        p["life"] -= 1
        
        alpha = int(255 * (p["life"] / 30))
        color = (*p["color"][:3], alpha) if len(p["color"]) == 4 else (*p["color"], alpha)
        
        pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), 2)
        
        if p["life"] <= 0:
            particles.remove(p)

# Основной игровой цикл
running = True
while running:
    screen.fill((10, 10, 30))  # Тёмно-синий фон
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                # Рестарт игры
                game_over = False
                score = 0
                lives = 3
                level = 1
                objects.clear()
                particles.clear()
                combo = 0
    
    if not game_over:
        # Управление игроком (с учётом бонуса скорости)
        current_speed = player_speed * 1.5 if bonuses["speed"]["active"] else player_speed
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= current_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
            player_x += current_speed
        
        # Спавн объектов
        spawn_timer += 1
        if spawn_timer >= spawn_delay:
            spawn_object()
            spawn_timer = 0
        
        # Движение объектов и проверка столкновений
        for obj in objects[:]:
            obj.x += obj.speed
            
            # Если объект упал за экран
            if obj.x > HEIGHT + obj.radius:
                objects.remove(obj)
                if obj.type not in ["bomb", "slow_bomb", "mine", *bonuses.keys()]:
                    combo = 0  
                    lives -= 1
                    if lives <= 0:
                        game_over = True
         
            if check_collision(obj):
                if obj.type in ["apple", "banana"]:
                    points = obj.points
                    if bonuses["double_points"]["active"]:
                        points *= 3
                    score += points
                    combo += 1
                    max_combo = max(max_combo, combo)
                    create_particles(obj.y, obj.x, obj.color)
                elif obj.type in ["bomb", "mine"]:
                    if not player_invincible:
                        lives -= obj.damage
                        combo = 0
                        create_particles(obj.x, obj.y, RED, 20)
                        if lives <= 0:
                            game_over = True
                elif obj.type == "slow_bomb":
                    # Замедляем все объекты на 2 секунды
                    for o in objects:
                        o.speed = max(1, o.speed - 3)
                    create_particles(obj.x, obj.y, PURPLE, 15)
                elif obj.type.startswith("bonus_"):
                    bonus_type = obj.type.split("_")[1]
                    bonuses[bonus_type]["active"] = True
                    bonuses[bonus_type]["timer"] = bonuses[bonus_type]["duration"]
                    create_particles(obj.x, obj.y, obj.color, 25)
                
                objects.remove(obj)
        
        # Обновление бонусов
        player_invincible = bonuses["invincible"]["active"]
        for bonus in bonuses.values():
            if bonus["active"]:
                bonus["timer"] -= 1
                if bonus["timer"] <= 0:
                    bonus["active"] = False
        
        # Увеличение уровня
        if score >= level * 15:
            level += 1
            spawn_delay = max(20, spawn_delay - 3)
    
    # Отрисовка
    # 1. Частицы (под всеми объектами)
    update_particles()
    
    # 2. Объекты
    for obj in objects:
        obj.draw()
    
    # 3. Игрок (корзина)
    basket_color = BLUE if player_invincible else GREEN
    pygame.draw.rect(screen, basket_color, (player_x, player_y, player_width, player_height))
    
    # 4. Интерфейс
    score_text = font_large.render(f"Счёт: {score}", True, WHITE)
    lives_text = font_large.render(f"♥ {lives}", True, RED)
    level_text = font_large.render(f"Ур. {level}", True, YELLOW)
    combo_text = font_small.render(f"Комбо: {combo} (Макс: {max_combo})", True, WHITE)
    
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (WIDTH - 99, 10))
    screen.blit(level_text, (WIDTH // 2 - 30, 10))
    screen.blit(combo_text, (10, 50))
    
    # Отображение активных бонусов
    bonus_y = 80
    for name, data in bonuses.items():
        if data["active"]:
            text = font_small.render(f"{name}: {data['timer'] // 70 + 2}с", True, data["color"])
            screen.blit(text, (10, bonus_y))
            bonus_y += 25
    
    if game_over:
        game_over_text = font_large.render("GAME OVER! Нажми R", True, RED)
        screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2 - 50))
        stats_text = font_small.render(f"Итог: Счёт {score}, Комбо {max_combo}", True, WHITE)
        screen.blit(stats_text, (WIDTH // 2 - 100, HEIGHT // 2 + 10))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
