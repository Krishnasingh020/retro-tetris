# tetris_ascii_retro.py
import pygame
import random
import sys

pygame.init()

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
CELL_SIZE = 30
COLS = 10
ROWS = 20
PLAYFIELD_W = COLS * CELL_SIZE
PLAYFIELD_H = ROWS * CELL_SIZE

WIDTH = 400
TOP_PAD = 50
SIDE_PAD = (WIDTH - PLAYFIELD_W) // 2
HEIGHT = TOP_PAD + PLAYFIELD_H + 40

FPS = 60

# Colors (monochrome green terminal)
BLACK = (0, 0, 0)
GREEN = (0, 220, 100)  # tweak for look you like
DIM_GREEN = (20, 60, 20)

# Fonts
font_title = pygame.font.SysFont("couriernew", 40, bold=True)
font_block = pygame.font.SysFont("couriernew", 22, bold=True)
font_dot = pygame.font.SysFont("couriernew", 14, bold=False)
font_small = pygame.font.SysFont("couriernew", 18, bold=False)

# Screen & clock
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro ASCII Tetris")
clock = pygame.time.Clock()

# ---------------------------------------------------------
# SHAPES (coordinate lists)
# coordinates are (x, y) relative to piece origin
# ---------------------------------------------------------
SHAPES = {
    'I': [(0,0), (1,0), (2,0), (3,0)],
    'O': [(0,0), (1,0), (0,1), (1,1)],
    'T': [(0,0), (1,0), (2,0), (1,1)],
    'S': [(1,0), (2,0), (0,1), (1,1)],
    'Z': [(0,0), (1,0), (1,1), (2,1)],
    'J': [(0,0), (0,1), (1,1), (2,1)],
    'L': [(2,0), (0,1), (1,1), (2,1)],
}

def new_piece():
    key = random.choice(list(SHAPES.keys()))
    # return a copy of the shape list so we don't mutate the global shape
    blocks = [(x, y) for (x, y) in SHAPES[key]]
    start_x = COLS // 2 - 2
    start_y = -1  # start slightly above the visible grid
    return key, blocks, start_x, start_y

# ---------------------------------------------------------
# Board & helpers
# ---------------------------------------------------------
board = [[None for _ in range(COLS)] for _ in range(ROWS)]  # None = empty, True = filled

def check_collision(blocks, off_x, off_y):
    """Return True if placing blocks at (off_x, off_y) collides with walls, floor or locked cells."""
    for x, y in blocks:
        gx = x + off_x
        gy = y + off_y
        # walls
        if gx < 0 or gx >= COLS:
            return True
        # floor
        if gy >= ROWS:
            return True
        # locked cells (only check if inside visible board)
        if gy >= 0 and board[gy][gx] is not None:
            return True
    return False

def lock_piece(blocks, off_x, off_y):
    """Lock blocks (mark board) — ignores blocks above top."""
    for x, y in blocks:
        gx = x + off_x
        gy = y + off_y
        if 0 <= gy < ROWS and 0 <= gx < COLS:
            board[gy][gx] = True

def clear_lines():
    """Clear full lines, return number cleared."""
    global board
    new_board = [row for row in board if any(cell is None for cell in row)]
    cleared = ROWS - len(new_board)
    for _ in range(cleared):
        new_board.insert(0, [None]*COLS)
    board = new_board
    return cleared

# ---------------------------------------------------------
# Drawing helpers (ASCII blocks & dot background)
# ---------------------------------------------------------
# Pre-render dot and block surfaces to reduce per-frame cost
dot_surf = font_dot.render(".", True, GREEN)
block_surf = font_block.render("[]", True, GREEN)

def draw_background(surface):
    """Draw dot grid background (centered in each cell)."""
    for r in range(ROWS):
        for c in range(COLS):
            px = SIDE_PAD + c * CELL_SIZE + (CELL_SIZE - dot_surf.get_width()) // 2
            py = TOP_PAD + r * CELL_SIZE + (CELL_SIZE - dot_surf.get_height()) // 2
            surface.blit(dot_surf, (px, py))

def draw_locked(surface):
    """Draw locked pieces as '[]' in green."""
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] is not None:
                px = SIDE_PAD + c * CELL_SIZE + (CELL_SIZE - block_surf.get_width()) // 2
                py = TOP_PAD + r * CELL_SIZE + (CELL_SIZE - block_surf.get_height()) // 2
                surface.blit(block_surf, (px, py))

def draw_piece(surface, blocks, off_x, off_y):
    """Draw falling piece as '[]'. Only draw cells that are visible (gy >= 0)."""
    for x, y in blocks:
        gx = x + off_x
        gy = y + off_y
        px = SIDE_PAD + gx * CELL_SIZE + (CELL_SIZE - block_surf.get_width()) // 2
        py = TOP_PAD + gy * CELL_SIZE + (CELL_SIZE - block_surf.get_height()) // 2
        if gy >= 0:  # only draw visible rows
            surface.blit(block_surf, (px, py))

# ---------------------------------------------------------
# Game state
# ---------------------------------------------------------
current_key, current_blocks, shape_x, shape_y = new_piece()
fall_speed = 500  # ms between automatic drops
last_fall = pygame.time.get_ticks()
score = 0
game_over = False

# ---------------------------------------------------------
# Main loop
# ---------------------------------------------------------
while True:
    if game_over:
        # simple game over screen
        screen.fill(BLACK)
        go_text = font_title.render("GAME OVER", True, GREEN)
        sc_text = font_small.render(f"Score: {score}", True, GREEN)
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 40))
        screen.blit(sc_text, (WIDTH//2 - sc_text.get_width()//2, HEIGHT//2 + 10))
        pygame.display.flip()
        pygame.time.wait(2500)
        pygame.quit()
        sys.exit()

    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    # --- events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if not check_collision(current_blocks, shape_x - 1, shape_y):
                    shape_x -= 1
            elif event.key == pygame.K_RIGHT:
                if not check_collision(current_blocks, shape_x + 1, shape_y):
                    shape_x += 1
            elif event.key == pygame.K_DOWN:
                # soft move down by one cell if possible
                if not check_collision(current_blocks, shape_x, shape_y + 1):
                    shape_y += 1
            elif event.key == pygame.K_SPACE:
                # hard drop
                while not check_collision(current_blocks, shape_x, shape_y + 1):
                    shape_y += 1
                # lock immediately
                lock_piece(current_blocks, shape_x, shape_y)
                lines = clear_lines()
                if lines:
                    # simple scoring table
                    score += [0, 100, 300, 500, 800][min(lines,4)]
                current_key, current_blocks, shape_x, shape_y = new_piece()
                # spawn collision -> game over
                if check_collision(current_blocks, shape_x, shape_y):
                    game_over = True
            # Note: rotation not implemented here (we can add next)

    # --- gravity (single source) ---
    if now - last_fall > fall_speed:
        if not check_collision(current_blocks, shape_x, shape_y + 1):
            shape_y += 1
        else:
            # lock & spawn
            lock_piece(current_blocks, shape_x, shape_y)
            lines = clear_lines()
            if lines:
                score += [0, 100, 300, 500, 800][min(lines,4)]
            current_key, current_blocks, shape_x, shape_y = new_piece()
            # immediate collision when spawning = game over
            if check_collision(current_blocks, shape_x, shape_y):
                game_over = True
        last_fall = now

    # --- draw ---
    screen.fill(BLACK)

    # title
    title = font_title.render("TETRIS", True, GREEN)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 6))

    # draw dotted background, locked blocks, current piece, HUD
    draw_background(screen)
    draw_locked(screen)
    draw_piece(screen, current_blocks, shape_x, shape_y)

    # HUD: score
    score_text = font_small.render(f"SCORE: {score}", True, GREEN)
    screen.blit(score_text, (10, 10))

    pygame.display.flip()
