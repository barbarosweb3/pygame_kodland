import pgzrun
import random
import math
import os
import sys
import pygame

try:
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per Monitor V2
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback
except ImportError:
    print("DPI Awareness ayarlanamadı")


def prepare_game_assets():
    # Klasörleri oluştur
    os.makedirs('images', exist_ok=True)
    os.makedirs('sounds', exist_ok=True)


    def create_image(filename, color1, color2):
        import pygame
        surface = pygame.Surface((50, 50), pygame.SRCALPHA)
        surface.fill(color1)
        pygame.draw.rect(surface, color2, (10, 10, 30, 30))
        pygame.image.save(surface, os.path.join('images', filename))


    pygame.init()


    create_image('hero_idle1.png', (0, 255, 0), (0, 0, 255))
    create_image('hero_idle2.png', (0, 255, 0), (0, 0, 255))
    create_image('hero_walk1.png', (0, 255, 0), (0, 0, 255))
    create_image('hero_walk2.png', (0, 255, 0), (0, 0, 255))
    create_image('enemy_idle1.png', (255, 0, 0), (0, 0, 0))
    create_image('enemy_idle2.png', (255, 0, 0), (0, 0, 0))
    create_image('enemy_walk1.png', (255, 0, 0), (0, 0, 0))
    create_image('enemy_walk2.png', (255, 0, 0), (0, 0, 0))



WIDTH = 800
HEIGHT = 600
TITLE = "Orman Macerası"


WHITE = pygame.Color('white')
BLACK = pygame.Color('black')
RED = pygame.Color('red')
GREEN = pygame.Color('green')
BLUE = pygame.Color('blue')


MENU = 0
PLAYING = 1
GAME_OVER = 2


class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover_color = pygame.Color(
            max(0, color.r - 50),
            max(0, color.g - 50),
            max(0, color.b - 50)
        )
        self.current_color = color

    def draw(self):
        screen.draw.filled_rect(self.rect, self.current_color)
        screen.draw.text(self.text, (self.rect.x + 10, self.rect.y + 10), color=self.text_color)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update_hover(self, pos):
        if self.rect.collidepoint(pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color


class Character:
    def __init__(self, x, y, image_names):
        self.x = x
        self.y = y
        self.images = [Actor(name) for name in image_names]
        self.current_image = 0
        self.animation_timer = 0
        self.animation_speed = 10

    def animate(self):
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.current_image = (self.current_image + 1) % len(self.images)
            self.animation_timer = 0

    def draw(self):
        self.animate()
        current_actor = self.images[self.current_image]
        current_actor.x = self.x
        current_actor.y = self.y
        current_actor.draw()


class Hero(Character):
    def __init__(self, x, y):
        hero_images = [
            'hero_idle1',
            'hero_idle2',
            'hero_walk1',
            'hero_walk2'
        ]
        super().__init__(x, y, hero_images)
        self.health = 100
        self.speed = 5

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed
        # Python 3.13.1 sınır kontrolleri
        self.x = max(0, min(self.x, WIDTH - self.images[0].width))
        self.y = max(0, min(self.y, HEIGHT - self.images[0].height))


class Enemy(Character):
    def __init__(self, x, y):
        enemy_images = [
            'enemy_idle1',
            'enemy_idle2',
            'enemy_walk1',
            'enemy_walk2'
        ]
        super().__init__(x, y, enemy_images)
        self.speed = 2
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.move_timer = 0
        self.move_interval = random.randint(50, 150)

    def update(self):
        self.move_timer += 1
        if self.move_timer >= self.move_interval:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            self.move_timer = 0

        dx, dy = self.direction
        self.x += dx * self.speed
        self.y += dy * self.speed

        self.x = max(0, min(self.x, WIDTH - self.images[0].width))
        self.y = max(0, min(self.y, HEIGHT - self.images[0].height))



game_state = MENU
hero = None
enemies = []


start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Oyuna Başla")
music_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Müzik: Açık")
exit_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 50, "Çıkış")


def init_game():
    global hero, enemies, game_state
    hero = Hero(WIDTH // 2, HEIGHT // 2)
    enemies = [
        Enemy(100, 100),
        Enemy(700, 500)
    ]
    game_state = PLAYING


def draw():
    screen.clear()

    if game_state == MENU:
        screen.fill(BLACK)
        start_button.draw()
        music_button.draw()
        exit_button.draw()
        screen.draw.text("Orman Macerası", (WIDTH // 2 - 100, HEIGHT // 4), color=WHITE, fontsize=50)

    elif game_state == PLAYING:
        screen.fill(GREEN)
        hero.draw()
        for enemy in enemies:
            enemy.draw()

        screen.draw.filled_rect(pygame.Rect(10, 10, hero.health * 2, 20), RED)

    elif game_state == GAME_OVER:
        screen.fill(BLACK)
        screen.draw.text("Oyun Bitti!", (WIDTH // 2 - 100, HEIGHT // 2), color=WHITE, fontsize=50)
        exit_button.draw()


def update():
    global game_state

    if game_state == PLAYING:
        if keyboard.left:
            hero.move(-1, 0)
        if keyboard.right:
            hero.move(1, 0)
        if keyboard.up:
            hero.move(0, -1)
        if keyboard.down:
            hero.move(0, 1)

        for enemy in enemies:
            enemy.update()

            if (abs(hero.x - enemy.x) < 50 and abs(hero.y - enemy.y) < 50):
                hero.health -= 1
                if hero.health <= 0:
                    game_state = GAME_OVER


def on_mouse_down(pos):
    global game_state

    if game_state == MENU:
        if start_button.is_clicked(pos):
            init_game()

        if music_button.is_clicked(pos):
            music_button.text = "Müzik: Kapalı" if music_button.text == "Müzik: Açık" else "Müzik: Açık"

        if exit_button.is_clicked(pos):
            pygame.quit()
            sys.exit()

    elif game_state == GAME_OVER:
        if exit_button.is_clicked(pos):
            pygame.quit()
            sys.exit()


def on_mouse_move(pos):
    if game_state == MENU:
        start_button.update_hover(pos)
        music_button.update_hover(pos)
        exit_button.update_hover(pos)



def on_key_down(key):
    if key == keys.ESCAPE:
        pygame.quit()
        sys.exit()



def init():
    prepare_game_assets()


init()
pgzrun.go()