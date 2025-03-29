import math
import pygame
from pygame import font
import cv2
import numpy as np
import os
import sys
from fighter import Fighter
from ml_model import behavior_tracker, cpu_model


def resource_path(relative_path):
    try:
        base_path=sys._MEIPASS
    except Exception:
        base_path=os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()

# Constants
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
FPS = 60
ROUND_OVER_COOLDOWN = 6000
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)


players = ["1", "2", "3", "4", "5"]  
selected_player = players[0]  # Default to the first player


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Street Fighter")
clock = pygame.time.Clock()

bg_image = cv2.imread(resource_path("assets/images/bg.jpg"))
victory_img = pygame.image.load(resource_path("assets/images/victory.png")).convert_alpha()
warrior_victory_img = pygame.image.load(resource_path("assets/images/trophy.png")).convert_alpha()
wizard_victory_img = pygame.image.load(resource_path("assets/images/wizard.png")).convert_alpha()
gameover_img = pygame.image.load(resource_path("assets/images/gameover.png")).convert_alpha()

menu_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 50)
menu_font_title = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 100)
count_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 80)
score_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), 30)

warrior_sheet = pygame.image.load(resource_path("assets/images/warrior.png")).convert_alpha()
wizard_sheet = pygame.image.load(resource_path("assets/images/wizard.png")).convert_alpha()

# Animations
WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 46]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 97]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

# Scores [P1, P2]
score = [0, 0]

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))
def blur_bg(image):
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    blurred_image = cv2.GaussianBlur(image_bgr, (15, 15), 0)
    return cv2.cvtColor(blurred_image, cv2.COLOR_BGR2RGB)
def draw_bg(image, is_game_started=False):
    if not is_game_started:
        blurred_bg=blur_bg(image)
        blurred_bg=pygame.surfarray.make_surface(np.transpose(blurred_bg, (1, 0, 2)))
        blurred_bg=pygame.transform.scale(blurred_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(blurred_bg, (0, 0))
    else:
        image = pygame.surfarray.make_surface(np.transpose(image, (1, 0, 2)))
        image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(image, (0, 0))

def draw_button(text, font, text_col, button_col, x, y, width, height):
    pygame.draw.rect(screen, button_col, (x, y, width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
    text_img = font.render(text, True, text_col)
    text_rect = text_img.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_img, text_rect)
    return pygame.Rect(x, y, width, height)

def victory_screen(winner_img):
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < ROUND_OVER_COOLDOWN:
        resized_victory_img = pygame.transform.scale(victory_img, 
                                    (victory_img.get_width() * 2, victory_img.get_height() * 2))
        screen.blit(resized_victory_img, (SCREEN_WIDTH // 2 - resized_victory_img.get_width() // 2,
                                          SCREEN_HEIGHT // 2 - resized_victory_img.get_height() // 2 - 50))
        screen.blit(winner_img, (SCREEN_WIDTH // 2 - winner_img.get_width() // 2,
                                 SCREEN_HEIGHT // 2 - winner_img.get_height() // 2 + 100))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
def game_over_screen(gameover_img):
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < ROUND_OVER_COOLDOWN:
        resized_gameover_img = pygame.transform.scale(
            gameover_img, 
            (gameover_img.get_width() // 2, gameover_img.get_height() // 2)
        )
        screen.blit(resized_gameover_img, (
            SCREEN_WIDTH // 2 - resized_gameover_img.get_width() // 2,
            SCREEN_HEIGHT // 2 - resized_gameover_img.get_height() // 2 - 50
        ))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
def draw_gradient_text(text, font, x, y, colors):
    offset = 2
    for i, color in enumerate(colors):
        img = font.render(text, True, color)
        screen.blit(img, (x + i * offset, y + i * offset))

def is_button_clicked(button_rect):
    mouse_pos = pygame.mouse.get_pos()
    return button_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]

def main_menu():
    global selected_player
    animation_start_time = pygame.time.get_ticks()
    while True:
        draw_bg(bg_image, is_game_started=False)
        elapsed_time = (pygame.time.get_ticks() - animation_start_time) / 1000
        scale_factor = 1 + 0.05 * math.sin(elapsed_time * 2 * math.pi)
        scaled_font = pygame.font.Font(resource_path("assets/fonts/turok.ttf"), int(100 * scale_factor))
        title_text = "STREET FIGHTER"
        colors = [BLUE, GREEN, YELLOW]
        title_x = SCREEN_WIDTH // 2-scaled_font.size(title_text)[0] // 2
        title_y = SCREEN_HEIGHT//6
        draw_gradient_text(title_text, scaled_font, title_x, title_y, colors)
        button_width = 280
        button_height = 60
        button_spacing = 30
        start_button_y = SCREEN_HEIGHT // 2 -(button_height + button_spacing) * 1.5 + 50
        select_player_button_y = SCREEN_HEIGHT // 2 - button_height // 2 + 50
        scores_button_y = SCREEN_HEIGHT // 2 + (button_height + button_spacing)*0.5 + 50
        exit_button_y = SCREEN_HEIGHT // 2 + (button_height + button_spacing) * 1.5+50

        # Buttons
        start_button = draw_button("START GAME", menu_font, BLACK, GREEN,
                                   SCREEN_WIDTH // 2 - button_width // 2,start_button_y, button_width, button_height)

        select_player_button = draw_button(f"PLAYER: {selected_player}",menu_font,BLACK, GREEN,
                                           SCREEN_WIDTH // 2 - button_width // 2, select_player_button_y,
                                           button_width, button_height)

        scores_button = draw_button("SCORES", menu_font, BLACK, GREEN,
                                    SCREEN_WIDTH//2 - button_width // 2, scores_button_y,
                                    button_width, button_height)

        exit_button = draw_button("EXIT", menu_font, BLACK, GREEN,
                                  SCREEN_WIDTH // 2 - button_width // 2, exit_button_y,
                                  button_width, button_height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    return "START"

                if select_player_button.collidepoint(event.pos):
                    current_index = players.index(selected_player)
                    new_index = (current_index + 1) % len(players)
                    selected_player = players[new_index]
                    behavior_tracker.set_player(selected_player)  # Update ML tracker

                if scores_button.collidepoint(event.pos):
                    return "SCORES"

                if exit_button.collidepoint(event.pos):
                    pygame.quit()
                    exit()

        pygame.display.update()
        clock.tick(FPS)


def scores_screen():
    while True:
        draw_bg(bg_image)
        scores_title = "SCORES"
        draw_text(scores_title, menu_font_title, RED, SCREEN_WIDTH // 2 - menu_font_title.size(scores_title)[0] // 2, 50)
        score_font_large = pygame.font.Font("assets/fonts/turok.ttf", 60)
        p1_text=f"HackPSU: {score[0]}"
        p2_text=f"Scriptcaster: {score[1]}"
        shadow_offset=5
        p1_text_x=SCREEN_WIDTH // 2 - score_font_large.size(p1_text)[0] // 2
        p1_text_y=SCREEN_HEIGHT // 2 - 50
        draw_text(p1_text, score_font_large, BLACK, p1_text_x + shadow_offset, p1_text_y + shadow_offset)
        draw_gradient_text(p1_text, score_font_large, p1_text_x, p1_text_y, [BLUE, GREEN])
        p2_text_x=SCREEN_WIDTH // 2 - score_font_large.size(p2_text)[0] // 2
        p2_text_y=SCREEN_HEIGHT // 2 + 50
        draw_text(p2_text, score_font_large, BLACK, p2_text_x + shadow_offset, p2_text_y + shadow_offset)
        draw_gradient_text(p2_text, score_font_large, p2_text_x, p2_text_y, [RED, YELLOW])
        return_button = draw_button("RETURN TO MAIN MENU", menu_font, BLACK, GREEN, SCREEN_WIDTH // 2 - 220, 700, 500, 50)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if return_button.collidepoint(event.pos):
                    return
        pygame.display.update()
        clock.tick(FPS)

def reset_game():
    global fighter_1, fighter_2
    fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS)
    fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS, is_cpu=True)

def draw_health_bar(health, x, y):
    pygame.draw.rect(screen, BLACK, (x, y, 200, 20))
    if health > 0:
        pygame.draw.rect(screen, RED, (x, y, health * 2, 20))
    pygame.draw.rect(screen, WHITE, (x, y, 200, 20), 2)

def countdown():
    countdown_font = pygame.font.Font("assets/fonts/turok.ttf", 100)
    countdown_texts = ["3", "2", "1", "FIGHT!"]
    for text in countdown_texts:
        draw_bg(bg_image, is_game_started=True)
        text_img = countdown_font.render(text, True, RED)
        text_width = text_img.get_width()
        x_pos = (SCREEN_WIDTH - text_width) // 2
        draw_text(text, countdown_font, RED, x_pos, SCREEN_HEIGHT // 2 - 50)
        pygame.display.update()
        pygame.time.delay(1000)

def game_loop():
    global score
    reset_game()
    round_over = False
    winner_img = None
    game_started = True
    countdown()
    while True:
        draw_bg(bg_image, is_game_started=game_started)
        draw_text(f"HackPSU: {score[0]}", score_font, RED, 20, 20)
        draw_text(f"Scriptcaster: {score[1]}", score_font, RED, SCREEN_WIDTH - 220, 20)
        draw_text("WAD for Movement, R and T for Attack", score_font, RED, SCREEN_WIDTH // 2 - 250, 100)
        draw_health_bar(fighter_1.health, 20, 50)
        draw_health_bar(fighter_2.health, SCREEN_WIDTH - 220, 50)
        exit_button = draw_button("MAIN MENU", menu_font, BLACK, YELLOW, SCREEN_WIDTH // 2 - 150, 20, 300, 50)
        if not round_over:
            fighter_1.move(SCREEN_WIDTH, SCREEN_HEIGHT, fighter_2, round_over)
            fighter_2.move(SCREEN_WIDTH, SCREEN_HEIGHT, fighter_1, round_over)
            fighter_1.update()
            fighter_2.update()

            # Log player 1 behavior for ML tracking
            behavior_tracker.log({
                "player_x": fighter_1.rect.x,
                "player_y": fighter_1.rect.y,
                "cpu_x": fighter_2.rect.x,
                "cpu_y": fighter_2.rect.y,
                "player_velocity": 10 if fighter_1.running else 0
                    }, fighter_1.action)
            if not fighter_1.alive:
                score[1] += 1
                round_over = True
                game_over_screen(gameover_img)
                return
            elif not fighter_2.alive:
                score[0] += 1
                round_over = True
                winner_img = warrior_victory_img
        else:
            # Train cpu using behavior data
            X, y = behavior_tracker.get_training_data()
            if X is not None and len(X) > 10:
                cpu_model.train(X, y)
                behavior_tracker.save_to_csv()
            victory_screen(winner_img)
            return
        fighter_1.draw(screen)
        fighter_2.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if exit_button.collidepoint(event.pos):
                    return
        pygame.display.update()
        clock.tick(FPS)

while True:
    menu_selection = main_menu()
    if menu_selection == "START":
        game_loop()
    elif menu_selection == "SCORES":
        scores_screen()
