import pygame
import sys
import os
import asyncio
import multiprocessing
from chatbot_app import run_chatbot_app

# --- Configuration ---
WIDTH, HEIGHT = 1280, 720
FONT_SIZE_QUEST = 36
FONT_SIZE_CHALLENGE = 48
FONT_SIZE_EDITOR = 36
FONT_SIZE_LARGE = 100
FONT_SIZE_MEDIUM = 60
FONT_SIZE_MAP = 50

# --- Colors ---
COLOR_BG = "#1a1a2e"
COLOR_UI_BG = (0, 0, 0, 128)
COLOR_TEXT = "#F2E9E4"
COLOR_GOLD = "gold"
COLOR_YELLOW = "yellow"
COLOR_WHITE = "white"
COLOR_RED = "red"
COLOR_XP_BAR_BG = "#4a4a6a"
COLOR_XP_BAR_FILL = "#34d399"
COLOR_CHALLENGE_BG = "#22223B"
COLOR_CHALLENGE_BORDER = "#F2E9E4"

# --- Challenge & Quest Management ---
class Challenge:
    def __init__(self, quest_name, problem_text, correct_answer, xp_reward):
        self.quest_name = quest_name
        self.problem_text = problem_text
        self.correct_answer = correct_answer
        self.xp_reward = xp_reward

class QuestManager:
    def __init__(self, challenges):
        self.challenges = challenges
        self.current_challenge_index = 0

    def get_current_challenge(self):
        return self.challenges[self.current_challenge_index] if self.current_challenge_index < len(self.challenges) else None

    def advance_quest(self):
        self.current_challenge_index += 1

    def all_quests_complete(self):
        return self.current_challenge_index >= len(self.challenges)

# --- UI Elements ---
class CodeEditorBox(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, challenge):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.challenge = challenge
        self.lines = [""]
        self.line_index = 0
        self.char_index = 0
        
        self.font_problem = pygame.font.Font(None, FONT_SIZE_CHALLENGE)
        self.font_editor = pygame.font.Font(None, FONT_SIZE_EDITOR)
        self.font_info = pygame.font.Font(None, 24)
        
        self.show_error = False
        self.error_timer = 0
        self.ERROR_FLASH_DURATION = 500
        
        self.cursor_visible = True
        self.cursor_timer = 0
        self.CURSOR_BLINK_RATE = 500

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                user_code = "\n".join(self.lines)
                is_correct = "".join(user_code.split()) == "".join(self.challenge.correct_answer.split())
                if not is_correct:
                    self.trigger_error_flash()
                return is_correct
            elif event.key == pygame.K_RETURN:
                line_after_cursor = self.lines[self.line_index][self.char_index:]
                self.lines[self.line_index] = self.lines[self.line_index][:self.char_index]
                self.line_index += 1
                self.lines.insert(self.line_index, line_after_cursor)
                self.char_index = 0
            elif event.key == pygame.K_BACKSPACE:
                if self.char_index > 0:
                    current_line = self.lines[self.line_index]
                    self.lines[self.line_index] = current_line[:self.char_index-1] + current_line[self.char_index:]
                    self.char_index -= 1
                elif self.line_index > 0:
                    prev_line_len = len(self.lines[self.line_index - 1])
                    self.lines[self.line_index - 1] += self.lines.pop(self.line_index)
                    self.line_index -= 1
                    self.char_index = prev_line_len
            elif event.key == pygame.K_LEFT:
                if self.char_index > 0: self.char_index -= 1
                elif self.line_index > 0:
                    self.line_index -= 1
                    self.char_index = len(self.lines[self.line_index])
            elif event.key == pygame.K_RIGHT:
                if self.char_index < len(self.lines[self.line_index]): self.char_index += 1
                elif self.line_index < len(self.lines) - 1:
                    self.line_index += 1
                    self.char_index = 0
            elif event.key == pygame.K_UP:
                if self.line_index > 0:
                    self.line_index -= 1
                    self.char_index = min(self.char_index, len(self.lines[self.line_index]))
            elif event.key == pygame.K_DOWN:
                if self.line_index < len(self.lines) - 1:
                    self.line_index += 1
                    self.char_index = min(self.char_index, len(self.lines[self.line_index]))
            else:
                current_line = self.lines[self.line_index]
                self.lines[self.line_index] = current_line[:self.char_index] + event.unicode + current_line[self.char_index:]
                self.char_index += len(event.unicode)
        return None

    def trigger_error_flash(self):
        self.show_error = True
        self.error_timer = pygame.time.get_ticks()

    def update(self):
        if self.show_error and pygame.time.get_ticks() - self.error_timer > self.ERROR_FLASH_DURATION:
            self.show_error = False
        if pygame.time.get_ticks() - self.cursor_timer > self.CURSOR_BLINK_RATE:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = pygame.time.get_ticks()

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_CHALLENGE_BG, self.rect, border_radius=15)
        border_color = COLOR_RED if self.show_error else COLOR_CHALLENGE_BORDER
        pygame.draw.rect(screen, border_color, self.rect, 4, border_radius=15)
        
        words = self.challenge.problem_text.split(' ')
        lines, current_line = [], ""
        for word in words:
            if self.font_problem.size(current_line + word)[0] < self.rect.width - 60:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        y_offset = 0
        for i, line in enumerate(lines):
            text_surface = self.font_problem.render(line, True, COLOR_TEXT)
            screen.blit(text_surface, (self.rect.x + 30, self.rect.y + 30 + i * self.font_problem.get_height()))
        y_offset = len(lines) * self.font_problem.get_height()

        info_text = self.font_info.render("Press [Shift+Enter] to Run Code", True, COLOR_YELLOW)
        screen.blit(info_text, (self.rect.x + 30, self.rect.bottom - 40))
        
        editor_area_y_start = self.rect.y + y_offset + 40
        line_height = self.font_editor.get_height()
        for i, line_text in enumerate(self.lines):
            line_surface = self.font_editor.render(line_text, True, COLOR_TEXT)
            screen.blit(line_surface, (self.rect.x + 30, editor_area_y_start + i * line_height))
        
        if self.cursor_visible:
            line_up_to_cursor = self.lines[self.line_index][:self.char_index]
            cursor_x_offset = self.font_editor.size(line_up_to_cursor)[0]
            cursor_pos_x = self.rect.x + 30 + cursor_x_offset
            cursor_pos_y = editor_area_y_start + self.line_index * line_height
            cursor_rect = pygame.Rect(cursor_pos_x, cursor_pos_y, 2, line_height)
            pygame.draw.rect(screen, COLOR_TEXT, cursor_rect)

class HUD:
    def __init__(self, player_stats, quest_manager):
        self.player_stats = player_stats
        self.quest_manager = quest_manager
        self.font = pygame.font.Font(None, FONT_SIZE_QUEST)
        self.small_font = pygame.font.Font(None, 24)
        self.LEVEL_UP_FLASH_DURATION = 1000

    def draw(self, screen):
        hud_surface = pygame.Surface((300, 120), pygame.SRCALPHA)
        hud_surface.fill(COLOR_UI_BG)
        level_text_str = f"Level: {self.player_stats['level']}"
        level_color = COLOR_WHITE
        if self.player_stats['level_up_active']:
            if pygame.time.get_ticks() - self.player_stats['level_up_timer'] < self.LEVEL_UP_FLASH_DURATION:
                if (pygame.time.get_ticks() // 200) % 2 == 0: level_color = COLOR_GOLD
            else: self.player_stats['level_up_active'] = False
        level_text = self.font.render(level_text_str, True, level_color)
        hud_surface.blit(level_text, (10, 5))
        xp_text = self.small_font.render(f"XP: {self.player_stats['xp']} / {self.player_stats['next_level_xp']}", True, COLOR_WHITE)
        hud_surface.blit(xp_text, (10, 45))
        xp_bar_rect = pygame.Rect(10, 70, 280, 15)
        pygame.draw.rect(hud_surface, COLOR_XP_BAR_BG, xp_bar_rect, border_radius=5)
        xp_percentage = self.player_stats['xp'] / self.player_stats['next_level_xp'] if self.player_stats['next_level_xp'] > 0 else 0
        fill_rect = pygame.Rect(xp_bar_rect.x, xp_bar_rect.y, xp_bar_rect.width * xp_percentage, xp_bar_rect.height)
        pygame.draw.rect(hud_surface, COLOR_XP_BAR_FILL, fill_rect, border_radius=5)
        current_challenge = self.quest_manager.get_current_challenge()
        quest_text_str = f"Objective: {current_challenge.quest_name}" if current_challenge else "Kingdom Cleared!"
        quest_text = self.small_font.render(quest_text_str, True, COLOR_WHITE)
        hud_surface.blit(quest_text, (10, 95))
        screen.blit(hud_surface, (20, 20))

# --- Game Sprites ---
class Player(pygame.sprite.Sprite):
    def __init__(self, animations, pos):
        super().__init__()
        self.animations = animations
        self.status = 'idle'
        self.current_frame = 0
        self.image = self.animations[self.status][self.current_frame]
        self.rect = self.image.get_rect(midbottom=pos)
        self.pos = pygame.math.Vector2(self.rect.midbottom)
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 5
        self.facing_right = True
        self.animation_timer = 0
        self.animation_speed = 100

    def set_pos(self, pos):
        self.pos = pygame.math.Vector2(pos)
        self.rect.midbottom = self.pos

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if self.direction.x > 0: self.facing_right = True
        elif self.direction.x < 0: self.facing_right = False

    def animate(self, dt):
        self.status = 'walk' if self.direction.length() != 0 else 'idle'
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            animation_frames = self.animations[self.status]
            self.current_frame = (self.current_frame + 1) % len(animation_frames)
            new_image = animation_frames[self.current_frame]
            self.image = pygame.transform.flip(new_image, not self.facing_right, False)

    def move(self):
        if self.direction.length() > 0: self.direction.normalize_ip()
        self.pos += self.direction * self.speed
        self.rect.midbottom = self.pos

    def update(self, dt):
        self.get_input()
        self.animate(dt)
        self.move()

class Boss(pygame.sprite.Sprite):
    def __init__(self, pos, image):
        super().__init__()
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect(midbottom=pos)
        self.pos = pos
        self.is_hit = False
        self.hit_timer = 0
        self.HIT_SHAKE_DURATION = 500

    def set_image(self, image):
        self.image = image
        self.original_image = image
        self.rect = self.image.get_rect(midbottom=self.pos)
        
    def set_pos(self, pos):
        self.pos = pos
        self.rect.midbottom = self.pos

    def get_hit(self):
        self.is_hit = True
        self.hit_timer = pygame.time.get_ticks()

    def update(self):
        if self.is_hit:
            if pygame.time.get_ticks() - self.hit_timer < self.HIT_SHAKE_DURATION:
                self.rect.centerx = self.pos[0] + (pygame.time.get_ticks() % 100 // 25 - 2) * 5
            else:
                self.is_hit = False
                self.rect.midbottom = self.pos

class Weapon(pygame.sprite.Sprite):
    def __init__(self, pos, image, target_pos):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        direction = pygame.math.Vector2(target_pos) - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * 15
        else:
            self.velocity = pygame.math.Vector2(0,0)
    
    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        if not pygame.display.get_surface().get_rect().colliderect(self.rect):
            self.kill()

class MapIcon(pygame.sprite.Sprite):
    def __init__(self, pos, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)

# --- Asset Loading ---
def load_all_animations(base_path, screen_height):
    animations = {}
    sprite_height = int(screen_height * 0.2)
    if not os.path.exists(base_path) or not os.listdir(base_path):
        placeholder = pygame.Surface((int(sprite_height * 0.75), sprite_height), pygame.SRCALPHA)
        placeholder.fill((255, 105, 180))
        return {'idle': [placeholder], 'walk': [placeholder]}
    
    for anim_type in os.listdir(base_path):
        anim_path = os.path.join(base_path, anim_type)
        if os.path.isdir(anim_path):
            frames = []
            for filename in sorted(os.listdir(anim_path)):
                if filename.endswith(".png"):
                    try:
                        image_path = os.path.join(anim_path, filename)
                        image = pygame.image.load(image_path).convert_alpha()
                        aspect_ratio = image.get_width() / image.get_height()
                        sprite_width = int(sprite_height * aspect_ratio)
                        image = pygame.transform.scale(image, (sprite_width, sprite_height))
                        frames.append(image)
                    except pygame.error as e:
                        print(f"Could not load image {filename}: {e}")
            if frames: animations[anim_type] = frames
    
    if 'idle' not in animations: animations['idle'] = [pygame.Surface((1,1), pygame.SRCALPHA)]
    if 'walk' not in animations: animations['walk'] = animations['idle']
    return animations

def load_image(path, size, fallback_color):
    try:
        return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
    except pygame.error:
        surface = pygame.Surface(size)
        surface.fill(fallback_color)
        return surface

# --- Main Game Function ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = screen.get_size()
    pygame.display.set_caption("Code Kingdoms")
    clock = pygame.time.Clock()

    # --- Load assets ---
    splash_image = load_image("frontpage.png", (WIDTH, HEIGHT), (20, 20, 40))
    map_image = load_image("bg.png", (WIDTH, HEIGHT), (20, 20, 40))
    python_level_bg = load_image("plains.jpg", (WIDTH, HEIGHT), (118, 184, 82))
    cpp_level_bg = load_image("castleswwwapizo.jpg", (WIDTH, HEIGHT), (135, 135, 135))
    c_level_bg = load_image("canyon.jpeg", (WIDTH, HEIGHT), (184, 118, 82))
    player_animations = load_all_animations("frames", HEIGHT)
    weapon_img = load_image("weapon.png", (60, 60), "cyan")
    hint_icon_img = load_image("hint_icon.png", (50, 50), (148, 0, 211))

    boss_size = (int(WIDTH * 0.15), int(HEIGHT * 0.25))
    python_boss_img = load_image("brrbrrpatapim.png", boss_size, "green")
    cpp_boss_img = load_image("boss.png", boss_size, "red")
    c_boss_img = load_image("bull boss.png", boss_size, "gray")

    # --- Kingdom Data ---
    python_curriculum = [
        Challenge("Learn Variables", "A variable 'score' needs to be set to 0.", "score=0", 50),
        Challenge("Learn Basic Math", "Increase 'score' by 10 (using shorthand).", "score+=10", 50),
        Challenge("Multi-line Code", "If age is 18 or over, print 'adult'.", "ifage>=18:print('adult')", 100),
    ]
    c_plus_plus_curriculum = [
        Challenge("C++ Variables", "Declare an integer 'health' and set it to 100.", "inthealth=100;", 75),
        Challenge("C++ Output", "Print 'Hello, Castle!' to the console.", "std::cout<<\"Hello,Castle!\";", 75),
    ]
    c_curriculum = [
        Challenge("C Pointers", "Declare an integer pointer named 'ptr'.", "int*ptr;", 100),
        Challenge("C Memory", "Allocate memory for 10 integers.", "malloc(10*sizeof(int))", 100),
    ]
    kingdoms = {
        "Python": {"curriculum": python_curriculum, "map_rect": pygame.Rect(WIDTH*0.05, HEIGHT*0.1, WIDTH*0.4, HEIGHT*0.4), "boss_img": python_boss_img, "boss_map_pos": (WIDTH*0.25, HEIGHT*0.3), "level_bg": python_level_bg},
        "C++": {"curriculum": c_plus_plus_curriculum, "map_rect": pygame.Rect(WIDTH*0.55, HEIGHT*0.05, WIDTH*0.4, HEIGHT*0.5), "boss_img": cpp_boss_img, "boss_map_pos": (WIDTH*0.75, HEIGHT*0.25), "level_bg": cpp_level_bg},
        "C": {"curriculum": c_curriculum, "map_rect": pygame.Rect(WIDTH*0.05, HEIGHT*0.6, WIDTH*0.4, HEIGHT*0.35), "boss_img": c_boss_img, "boss_map_pos": (WIDTH*0.25, HEIGHT*0.8), "level_bg": c_level_bg},
    }
    kingdom_progress = {name: False for name in kingdoms}

    # --- Player and Global State ---
    player_stats = {'level': 1, 'xp': 0, 'next_level_xp': 100, 'level_up_active': False, 'level_up_timer': 0}
    player = Player(player_animations, (0, 0))
    boss = Boss((0, 0), cpp_boss_img)
    player_group = pygame.sprite.GroupSingle(player)
    boss_group = pygame.sprite.GroupSingle(boss)
    weapon_group = pygame.sprite.Group()

    map_icon_size = (80, 80)
    map_player_icon = MapIcon((WIDTH * 0.9, HEIGHT * 0.9), pygame.transform.scale(player.image, map_icon_size))
    map_boss_icons = pygame.sprite.Group([MapIcon(data["boss_map_pos"], pygame.transform.scale(data["boss_img"], map_icon_size)) for data in kingdoms.values()])
    
    quest_manager, hud, challenge_box, current_kingdom_key = None, None, None, None
    chatbot_process, hint_button_rect = None, None

    big_font = pygame.font.Font(None, FONT_SIZE_LARGE)
    medium_font = pygame.font.Font(None, FONT_SIZE_MEDIUM)

    game_state, battle_stage, battle_timer = 'splash', 'forging', 0
    BATTLE_DURATIONS = {'forging': 500, 'attacking': 1000, 'impact': 300, 'victory': 1500}

    # --- Main Loop ---
    running = True
    while running:
        dt = clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            
            if game_state == 'splash' and (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN):
                game_state = 'world_map'
            
            elif game_state == 'world_map' and event.type == pygame.MOUSEBUTTONDOWN:
                for key, data in kingdoms.items():
                    if data["map_rect"].collidepoint(mouse_pos) and not kingdom_progress[key]:
                        current_kingdom_key = key
                        quest_manager = QuestManager(data["curriculum"])
                        hud = HUD(player_stats, quest_manager)
                        player.set_pos((WIDTH * 0.1, HEIGHT * 0.8))
                        boss.set_pos((WIDTH * 0.9, HEIGHT * 0.8))
                        boss.set_image(data["boss_img"])
                        game_state = 'level'
                        break

            elif game_state == 'challenge':
                if event.type == pygame.MOUSEBUTTONDOWN and hint_button_rect and hint_button_rect.collidepoint(event.pos):
                    if chatbot_process is None or not chatbot_process.is_alive():
                        print("Launching AI Assistant...")
                        current_challenge = quest_manager.get_current_challenge()
                        prompt = f"I need a hint for this problem: \"{current_challenge.problem_text}\"."
                        chatbot_process = multiprocessing.Process(target=run_chatbot_app, args=(prompt,))
                        chatbot_process.start()

                if challenge_box:
                    is_correct = challenge_box.handle_event(event)
                    if is_correct is True:
                        game_state = 'battle'
                        battle_stage = 'forging'
                        battle_timer = pygame.time.get_ticks()

        # --- Update Logic ---
        if game_state == 'level':
            player_group.update(dt)
            if pygame.sprite.spritecollide(player, boss_group, False) and not quest_manager.all_quests_complete():
                game_state = 'challenge'
                current_challenge = quest_manager.get_current_challenge()
                dialog_w, dialog_h = WIDTH * 0.8, HEIGHT * 0.6
                challenge_box = CodeEditorBox((WIDTH - dialog_w) / 2, (HEIGHT - dialog_h) / 2, dialog_w, dialog_h, current_challenge)
                # <<< FIX: Calculate the button's rect as soon as the challenge box is created.
                hint_button_rect = hint_icon_img.get_rect(topright=(challenge_box.rect.right - 15, challenge_box.rect.top + 15))
        
        elif game_state == 'challenge' and challenge_box:
            challenge_box.update()
        
        elif game_state == 'battle':
            boss_group.update()
            weapon_group.update()
            current_time = pygame.time.get_ticks()

            if battle_stage == 'forging' and current_time - battle_timer > BATTLE_DURATIONS['forging']:
                weapon = Weapon(player.rect.center, weapon_img, boss.rect.center)
                weapon_group.add(weapon)
                battle_stage = 'attacking'
                battle_timer = current_time 
            elif battle_stage == 'attacking' and (not weapon_group or current_time - battle_timer > BATTLE_DURATIONS['attacking']):
                 battle_stage = 'impact'
                 battle_timer = current_time
                 boss.get_hit()
                 weapon_group.empty()
            elif battle_stage == 'impact' and current_time - battle_timer > BATTLE_DURATIONS['impact']:
                battle_stage = 'victory'
                battle_timer = current_time
                reward = quest_manager.get_current_challenge().xp_reward
                player_stats['xp'] += reward
                if player_stats['xp'] >= player_stats['next_level_xp']:
                    player_stats['level'] += 1
                    player_stats['xp'] -= player_stats['next_level_xp']
                    player_stats['next_level_xp'] = int(player_stats['next_level_xp'] * 1.5)
                    player_stats['level_up_active'] = True
                    player_stats['level_up_timer'] = pygame.time.get_ticks()
                quest_manager.advance_quest()
            elif battle_stage == 'victory' and current_time - battle_timer > BATTLE_DURATIONS['victory']:
                if quest_manager.all_quests_complete():
                    kingdom_progress[current_kingdom_key] = True
                    game_state = 'world_map'
                    if all(kingdom_progress.values()): game_state = 'gameover'
                else:
                    game_state = 'level'

        # --- Drawing Logic ---
        screen.fill(COLOR_BG)
        if game_state == 'splash':
            screen.blit(splash_image, (0, 0))
        elif game_state == 'world_map':
            screen.blit(map_image, (0, 0))
            map_boss_icons.draw(screen)
            screen.blit(map_player_icon.image, map_player_icon.rect)
        elif game_state == 'gameover':
            screen.blit(map_image, (0, 0))
            title_text = big_font.render("VICTORY!", True, COLOR_GOLD)
            screen.blit(title_text, title_text.get_rect(center=(WIDTH/2, HEIGHT/2)))
        elif game_state in ['level', 'challenge', 'battle']:
            screen.blit(kingdoms[current_kingdom_key]['level_bg'], (0, 0))
            player_group.draw(screen)
            boss_group.draw(screen)
            if hud: hud.draw(screen)
            if game_state == 'challenge':
                challenge_box.draw(screen)
                # <<< FIX: Now we just draw the button; its rect is already calculated.
                if hint_button_rect:
                    screen.blit(hint_icon_img, hint_button_rect)
            elif game_state == 'battle':
                weapon_group.draw(screen)
                if battle_stage == 'forging':
                    text = medium_font.render("Forging Weapon...", True, COLOR_YELLOW)
                    screen.blit(text, text.get_rect(center=(WIDTH/2, HEIGHT/2)))
                elif battle_stage == 'victory':
                    text = big_font.render("SUCCESS!", True, COLOR_GOLD)
                    screen.blit(text, text.get_rect(center=(WIDTH/2, HEIGHT/2)))

        pygame.display.flip()
        await asyncio.sleep(0)

    if chatbot_process and chatbot_process.is_alive():
        chatbot_process.terminate()
        chatbot_process.join()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass
    asyncio.run(main())