# tetris_ascii_full.py  (complete file)
import pygame
import random
import os
import sys

pygame.init()
pygame.mixer.init()

# -----------------------
# CONFIG
# -----------------------
CELL_SIZE = 28
COLS = 10
ROWS = 20
PLAYFIELD_W = COLS * CELL_SIZE
PLAYFIELD_H = ROWS * CELL_SIZE

WIDTH = 560
SIDE_PAD = 40
TOP_PAD = 50
HEIGHT = TOP_PAD + PLAYFIELD_H + 40

FPS = 60

BLACK = (0, 0, 0)
GREEN = (0, 220, 120)
DIM_GREEN = (0, 80, 40)
GHOST_GREEN = (0, 160, 80)
HOLD_BOX_GREEN = (255, 255, 255)

font_title = pygame.font.SysFont("couriernew", 36, bold=True)
font_block = pygame.font.SysFont("couriernew", 22, bold=True)
font_dot = pygame.font.SysFont("couriernew", 14, bold=False)
font_small = pygame.font.SysFont("couriernew", 18, bold=False)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro ASCII Tetris — Green Terminal")
clock = pygame.time.Clock()

SHAPES = {
    'I': [(0,0),(1,0),(2,0),(3,0)],
    'O': [(0,0),(1,0),(0,1),(1,1)],
    'T': [(0,0),(1,0),(2,0),(1,1)],
    'S': [(1,0),(2,0),(0,1),(1,1)],
    'Z': [(0,0),(1,0),(1,1),(2,1)],
    'J': [(0,0),(0,1),(1,1),(2,1)],
    'L': [(2,0),(0,1),(1,1),(2,1)],
}

def safe_load_sound(name):
    try:
        path = os.path.join(os.path.dirname(__file__), name)
    except Exception:
        path = name
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None
    return None

sound_move = safe_load_sound("move.wav")
sound_rotate = safe_load_sound("rotate.wav")
sound_clear = safe_load_sound("clear.wav")
sound_gameover = safe_load_sound("gameover.wav")

def play_sound(snd):
    if snd:
        try:
            snd.play()
        except Exception:
            pass

board = [[None for _ in range(COLS)] for _ in range(ROWS)]

dot_surf = font_dot.render(".", True, DIM_GREEN)
block_surf = font_block.render("[]", True, GREEN)
ghost_surf = font_block.render("[]", True, GHOST_GREEN)
hold_label = font_small.render("HOLD", True, HOLD_BOX_GREEN)

def spawn_piece():
    key = random.choice(list(SHAPES.keys()))
    blocks = [(x, y) for x, y in SHAPES[key]]
    start_x = COLS // 2 - 2
    start_y = -1
    return key, blocks, start_x, start_y

def rotate_blocks(blocks):
    rotated = [(y, -x) for x, y in blocks]
    min_x = min(x for x, y in rotated)
    min_y = min(y for x, y in rotated)
    rotated = [(x - min_x, y - min_y) for x, y in rotated]
    return rotated

def check_collision(blocks, off_x, off_y):
    for x, y in blocks:
        gx = x + off_x
        gy = y + off_y
        if gx < 0 or gx >= COLS:
            return True
        if gy >= ROWS:
            return True
        if gy >= 0 and board[gy][gx] is not None:
            return True
    return False

def lock_piece(blocks, off_x, off_y):
    for x, y in blocks:
        gx = x + off_x
        gy = y + off_y
        if 0 <= gy < ROWS and 0 <= gx < COLS:
            board[gy][gx] = True

def clear_lines():
    global board
    new_board = [row for row in board if any(cell is None for cell in row)]
    cleared = ROWS - len(new_board)
    for _ in range(cleared):
        new_board.insert(0, [None]*COLS)
    board = new_board
    return cleared

def compute_ghost_y(blocks, off_x, off_y):
    gy = off_y
    while not check_collision(blocks, off_x, gy + 1):
        gy += 1
    return gy

def draw_dotted_background(surface):
    for r in range(ROWS):
        for c in range(COLS):
            px = SIDE_PAD + c * CELL_SIZE + (CELL_SIZE - dot_surf.get_width())//2
            py = TOP_PAD + r * CELL_SIZE + (CELL_SIZE - dot_surf.get_height())//2
            surface.blit(dot_surf, (px, py))

def draw_locked(surface):
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] is not None:
                px = SIDE_PAD + c * CELL_SIZE + (CELL_SIZE - block_surf.get_width())//2
                py = TOP_PAD + r * CELL_SIZE + (CELL_SIZE - block_surf.get_height())//2
                surface.blit(block_surf, (px, py))

def draw_piece_at(surface, blocks, off_x, off_y, surf):
    for x, y in blocks:
        gx = x + off_x
        gy = y + off_y
        if gy >= 0:
            px = SIDE_PAD + gx * CELL_SIZE + (CELL_SIZE - surf.get_width())//2
            py = TOP_PAD + gy * CELL_SIZE + (CELL_SIZE - surf.get_height())//2
            surface.blit(surf, (px, py))

def draw_hold_box(surface, hold_key):
    box_x = SIDE_PAD + PLAYFIELD_W + 16
    box_y = TOP_PAD + 20
    box_w = CELL_SIZE * 4
    box_h = CELL_SIZE * 4
    pygame.draw.rect(surface, HOLD_BOX_GREEN, (box_x - 6, box_y - 6, box_w + 12, box_h + 12), 2)
    surface.blit(hold_label, (box_x + 6, box_y - 6))
    if hold_key:
        sample = font_block.render(hold_key, True, GREEN)
        surface.blit(sample, (box_x + 8, box_y + box_h//2 - sample.get_height()//2))

def draw_scanlines(surface):
    scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(scan, (0,0,0,40), (0,y), (WIDTH,y))
    surface.blit(scan, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

def draw_vignette(surface):
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(glow, (0,40,0,30), (0,0,WIDTH,HEIGHT), border_radius=8)
    surface.blit(glow, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

# INITIAL STATE
current_key, current_blocks, shape_x, shape_y = spawn_piece()
hold_key = None
hold_blocks = None
can_hold = True  # disallow hold repeatedly without locking
fall_speed_ms = 500
last_fall = pygame.time.get_ticks()
score = 0
game_over = False

# INPUT autorepeat timers
move_repeat_delay = 160
move_repeat_rate = 60  # ms between repeats
last_move_time = 0
key_held = None

# Main game loop
while True:
    if game_over:
        screen.fill(BLACK)
        go_text = font_title.render("GAME OVER", True, GREEN)
        sc_text = font_small.render(f"Score: {score}", True, GREEN)
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 40))
        screen.blit(sc_text, (WIDTH//2 - sc_text.get_width()//2, HEIGHT//2 + 10))
        pygame.display.flip()
        play_sound(sound_gameover)
        pygame.time.wait(2500)
        pygame.quit()
        sys.exit()

    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if not check_collision(current_blocks, shape_x - 1, shape_y):
                    shape_x -= 1
                    play_sound(sound_move)
                key_held = 'left'
                last_move_time = now
            elif event.key == pygame.K_RIGHT:
                if not check_collision(current_blocks, shape_x + 1, shape_y):
                    shape_x += 1
                    play_sound(sound_move)
                key_held = 'right'
                last_move_time = now
            elif event.key == pygame.K_DOWN:
                if not check_collision(current_blocks, shape_x, shape_y + 1):
                    shape_y += 1
                    play_sound(sound_move)
            elif event.key == pygame.K_SPACE:
                # hard drop
                while not check_collision(current_blocks, shape_x, shape_y + 1):
                    shape_y += 1
                lock_piece(current_blocks, shape_x, shape_y)
                cleared = clear_lines()
                if cleared:
                    score += [0,100,300,500,800][min(cleared,4)]
                    play_sound(sound_clear)
                current_key, current_blocks, shape_x, shape_y = spawn_piece()
                if check_collision(current_blocks, shape_x, shape_y):
                    game_over = True
                can_hold = True
            elif event.key == pygame.K_UP:
                # rotate with small wall-kick attempts
                rotated = rotate_blocks(current_blocks)
                kicked = False
                kicks = [0, -1, 1, -2, 2]
                for k in kicks:
                    if not check_collision(rotated, shape_x + k, shape_y):
                        current_blocks = rotated
                        shape_x += k
                        kicked = True
                        play_sound(sound_rotate)
                        break
                # else rotation fails
            elif event.key == pygame.K_c:
                if can_hold:
                    # swap hold
                    if hold_key is None:
                        hold_key = current_key
                        hold_blocks = [(x,y) for x,y in current_blocks]
                        current_key, current_blocks, shape_x, shape_y = spawn_piece()
                    else:
                        # swap current with hold
                        tmp_key, tmp_blocks = hold_key, hold_blocks
                        hold_key, hold_blocks = current_key, [(x,y) for x,y in current_blocks]
                        current_key, current_blocks = tmp_key, [(x,y) for x,y in tmp_blocks]
                        shape_x = COLS // 2 - 2
                        shape_y = -1
                    can_hold = False
                    play_sound(sound_move)
            elif event.key == pygame.K_r:
                # restart quick (dev)
                board = [[None for _ in range(COLS)] for _ in range(ROWS)]
                current_key, current_blocks, shape_x, shape_y = spawn_piece()
                hold_key = None
                hold_blocks = None
                can_hold = True
                score = 0

        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                key_held = None

    # Key autorepeat for left/right
    if key_held and (now - last_move_time) > move_repeat_delay:
        if (now - last_move_time - move_repeat_delay) % move_repeat_rate < dt:
            if key_held == 'left':
                if not check_collision(current_blocks, shape_x - 1, shape_y):
                    shape_x -= 1
                    play_sound(sound_move)
            elif key_held == 'right':
                if not check_collision(current_blocks, shape_x + 1, shape_y):
                    shape_x += 1
                    play_sound(sound_move)

    # Gravity (single source)
    if now - last_fall > fall_speed_ms:
        if not check_collision(current_blocks, shape_x, shape_y + 1):
            shape_y += 1
        else:
            lock_piece(current_blocks, shape_x, shape_y)
            cleared = clear_lines()
            if cleared:
                score += [0,100,300,500,800][min(cleared,4)]
                play_sound(sound_clear)
            current_key, current_blocks, shape_x, shape_y = spawn_piece()
            if check_collision(current_blocks, shape_x, shape_y):
                game_over = True
            can_hold = True
        last_fall = now

    # Draw
    screen.fill(BLACK)
    title = font_title.render("TETRIS", True, GREEN)
    screen.blit(title, (SIDE_PAD, 8))

    # dotted background + locked + ghost + current + hold + HUD
    draw_dotted_background(screen)
    draw_locked(screen)

    # ghost
    ghost_y = compute_ghost_y(current_blocks, shape_x, shape_y)
    draw_piece_at(screen, current_blocks, shape_x, ghost_y, ghost_surf)

    # current piece
    draw_piece_at(screen, current_blocks, shape_x, shape_y, block_surf)

    # hold box
    draw_hold_box(screen, hold_key)

    # HUD: score
    score_text = font_small.render(f"SCORE: {score}", True, GREEN)
    screen.blit(score_text, (SIDE_PAD + PLAYFIELD_W - score_text.get_width(), 12))

    # retro CRT overlays
    draw_scanlines(screen)
    draw_vignette(screen)

    pygame.display.flip()

pygame.quit()
