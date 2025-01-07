import pgzrun
import random
import math
import os
import sys
import pygame
from enum import Enum
from dataclasses import dataclass

try:
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()
except ImportError:
    print("DPI Awareness ayarlanamadi")

WIDTH = 800
HEIGHT = 600
TITLE = "Orman Macerasi"


class Colors:
    WHITE = pygame.Color('white')
    BLACK = pygame.Color('black')
    RED = pygame.Color('red')
    GREEN = pygame.Color('green')
    BLUE = pygame.Color('blue')


class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2


class AssetManager:
    @staticmethod
    def create_image(filename, color1, color2):
        filepath = os.path.join('images', filename)
        if not os.path.exists(filepath):
            surface = pygame.Surface((50, 50), pygame.SRCALPHA)
            surface.fill(color1)
            pygame.draw.rect(surface, color2, (10, 10, 30, 30))
            pygame.image.save(surface, filepath)

    @staticmethod
    def create_test_audio():
        if not os.path.exists(os.path.join('music', 'background.wav')):
            import wave
            import struct

            with wave.open(os.path.join('music', 'background.wav'), 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(44100)
                for i in range(44100 * 2):  # 2 saniyelik ses
                    value = int(32767.0 * math.sin(i * 440.0 * 2.0 * math.pi / 44100.0))
                    data = struct.pack('<h', value)
                    f.writeframesraw(data)

        if not os.path.exists(os.path.join('sounds', 'hit.wav')):
            with wave.open(os.path.join('sounds', 'hit.wav'), 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(44100)
                for i in range(44100):  # 1 saniyelik ses
                    value = int(32767.0 * math.sin(i * 880.0 * 2.0 * math.pi / 44100.0))
                    data = struct.pack('<h', value)
                    f.writeframesraw(data)

    @staticmethod
    def prepare_game_assets():
        os.makedirs('images', exist_ok=True)
        os.makedirs('sounds', exist_ok=True)
        os.makedirs('music', exist_ok=True)

        AssetManager.create_test_audio()

        hero_colors = (Colors.GREEN, Colors.BLUE)
        enemy_colors = (Colors.RED, Colors.BLACK)

        for prefix, colors in [("hero", hero_colors), ("enemy", enemy_colors)]:
            for state in ["idle", "walk"]:
                for i in range(1, 3):
                    AssetManager.create_image(
                        f"{prefix}_{state}{i}.png",
                        colors[0],
                        colors[1]
                    )


class ButtonConfig:
    def __init__(self):
        self.width = 200
        self.height = 50
        self.default_color = Colors.BLUE
        self.text_color = Colors.WHITE


class Button:
    def __init__(self, x, y, text, config=ButtonConfig()):
        self.rect = pygame.Rect(x, y, config.width, config.height)
        self.text = text
        self.color = config.default_color
        self.text_color = config.text_color
        self.hover_color = pygame.Color(
            max(0, config.default_color.r - 50),
            max(0, config.default_color.g - 50),
            max(0, config.default_color.b - 50)
        )
        self.current_color = self.color

    def draw(self, screen):
        screen.draw.filled_rect(self.rect, self.current_color)
        screen.draw.text(
            self.text,
            (self.rect.x + 10, self.rect.y + 10),
            color=self.text_color
        )

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update_hover(self, pos):
        self.current_color = self.hover_color if self.rect.collidepoint(pos) else self.color


class Character:
    def __init__(self, x, y, image_names):
        self.pos = pygame.math.Vector2(x, y)
        self.images = [Actor(name) for name in image_names]
        self.current_image = 0
        self.animation_timer = 0
        self.animation_speed = 10
        self._rect = pygame.Rect(x, y, 50, 50)  # Varsayılan boyut
        self.update_rect()

    def animate(self):
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.current_image = (self.current_image + 1) % len(self.images)
            self.animation_timer = 0

    def draw(self, screen):
        self.animate()
        current_actor = self.images[self.current_image]
        current_actor.pos = self.pos
        current_actor.draw()

    def update_rect(self):
        self._rect.center = self.pos

    def colliderect(self, other):
        return self._rect.colliderect(other._rect)


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
        self.invincibility_timer = 0
        self.invincibility_duration = 30

    def move(self, dx, dy):
        movement = pygame.math.Vector2(dx, dy).normalize() * self.speed if (dx or dy) else pygame.math.Vector2()
        new_pos = self.pos + movement

        new_pos.x = max(0, min(new_pos.x, WIDTH - 50))  # 50 karakter genişliği
        new_pos.y = max(0, min(new_pos.y, HEIGHT - 50))  # 50 karakter yüksekliği

        self.pos = new_pos
        self.update_rect()

    def update(self):
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

    def take_damage(self, amount):
        if self.invincibility_timer <= 0:
            self.health -= amount
            self.invincibility_timer = self.invincibility_duration
            sounds.hit.play()
            return True
        return False


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
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.move_timer = 0
        self.move_interval = random.randint(50, 150)

    def update(self):
        self.move_timer += 1
        if self.move_timer >= self.move_interval:
            self.direction = pygame.math.Vector2(
                random.choice([-1, 1]),
                random.choice([-1, 1])
            ).normalize()
            self.move_timer = 0

        new_pos = self.pos + self.direction * self.speed

        new_pos.x = max(0, min(new_pos.x, WIDTH - 50))  # 50 karakter genişliği
        new_pos.y = max(0, min(new_pos.y, HEIGHT - 50))  # 50 karakter yüksekliği

        if new_pos.x in (0, WIDTH - 50) or new_pos.y in (0, HEIGHT - 50):
            self.direction *= -1

        self.pos = new_pos
        self.update_rect()


class GameManager:
    def __init__(self):
        self.state = GameState.MENU
        self.hero = None
        self.enemies = []
        self.setup_buttons()
        self.music_enabled = True
        self.setup_audio()

    def setup_buttons(self):
        center_x = WIDTH // 2 - 100
        self.start_button = Button(center_x, HEIGHT // 2 - 50, "Oyuna Basla")
        self.music_button = Button(center_x, HEIGHT // 2 + 50, "Muzik: Acik")
        self.exit_button = Button(center_x, HEIGHT // 2 + 150, "Cikis")

    def setup_audio(self):
        self.background_music = 'background.wav'  # music/background.wav dosyasını kullanır
        self.hit_sound = 'hit'  # sounds/hit.wav dosyasını kullanır
        if self.music_enabled:
            try:
                music.play(self.background_music)
                music.set_volume(0.5)
            except Exception as e:
                print(f"Müzik yüklenirken hata: {e}")

    def init_game(self):
        self.hero = Hero(WIDTH // 2, HEIGHT // 2)
        self.enemies = [
            Enemy(100, 100),
            Enemy(700, 500)
        ]
        self.state = GameState.PLAYING

    def update(self):
        if self.state == GameState.PLAYING:
            dx = keyboard.right - keyboard.left
            dy = keyboard.down - keyboard.up
            self.hero.move(dx, dy)
            self.hero.update()

            for enemy in self.enemies:
                enemy.update()
                if self.hero.colliderect(enemy):
                    if self.hero.take_damage(1):
                        if self.hero.health <= 0:
                            self.state = GameState.GAME_OVER

    def draw(self, screen):
        screen.clear()

        if self.state == GameState.MENU:
            screen.fill(Colors.BLACK)
            self.start_button.draw(screen)
            self.music_button.draw(screen)
            self.exit_button.draw(screen)
            screen.draw.text(
                TITLE,
                (WIDTH // 2 - 100, HEIGHT // 4),
                color=Colors.WHITE,
                fontsize=50
            )

        elif self.state == GameState.PLAYING:
            screen.fill(Colors.GREEN)
            self.hero.draw(screen)
            for enemy in self.enemies:
                enemy.draw(screen)

            screen.draw.filled_rect(
                pygame.Rect(10, 10, self.hero.health * 2, 20),
                Colors.RED
            )

        elif self.state == GameState.GAME_OVER:
            screen.fill(Colors.BLACK)
            screen.draw.text(
                "Oyun Bitti!",
                (WIDTH // 2 - 100, HEIGHT // 2),
                color=Colors.WHITE,
                fontsize=50
            )
            self.exit_button.draw(screen)

    def handle_click(self, pos):
        if self.state == GameState.MENU:
            if self.start_button.is_clicked(pos):
                self.init_game()
            elif self.music_button.is_clicked(pos):
                self.music_enabled = not self.music_enabled
                self.music_button.text = "Muzik: Kapali" if not self.music_enabled else "Muzik: Acik"
                if self.music_enabled:
                    music.unpause()
                else:
                    music.pause()
            elif self.exit_button.is_clicked(pos):
                self.exit_game()
        elif self.state == GameState.GAME_OVER:
            if self.exit_button.is_clicked(pos):
                self.exit_game()

    def handle_mouse_move(self, pos):
        if self.state == GameState.MENU:
            self.start_button.update_hover(pos)
            self.music_button.update_hover(pos)
            self.exit_button.update_hover(pos)

    @staticmethod
    def exit_game():
        pygame.quit()
        sys.exit()


game_manager = None


def init():
    global game_manager
    AssetManager.prepare_game_assets()
    game_manager = GameManager()


def draw():
    game_manager.draw(screen)


def update():
    game_manager.update()


def on_mouse_down(pos):
    game_manager.handle_click(pos)


def on_mouse_move(pos):
    game_manager.handle_mouse_move(pos)


def on_key_down(key):
    if key == keys.ESCAPE:
        GameManager.exit_game()


init()
pgzrun.go()