import pyglet
import random
from pyglet import shapes, text
from pyglet.window import key


def run_sar_mission_game():
    # --- Game Configuration ---
    WINDOW_WIDTH = 1600
    WINDOW_HEIGHT = 800
    CELL_SIZE = 20
    TOTAL_GRID_X = WINDOW_WIDTH // CELL_SIZE
    TOTAL_GRID_Y = WINDOW_HEIGHT // CELL_SIZE
    TIME_LIMIT = 300  # 5 minutes

    # --- Game State ---
    window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Mission")
    game_state = "menu"  # menu, view_select, difficulty_select, playing, game_over, game_over_time
    difficulty = None    # easy, medium, hard
    current_zoom = "global"
    selected_initial_view = "global"
    time_remaining = TIME_LIMIT

    # Zoom state
    MIN_ZOOM, MAX_ZOOM = 0.25, 1.50
    zoom_level = 1.00  # 1.0 = 100%

    # --- Batches for Rendering ---
    batch = pyglet.graphics.Batch()
    ui_batch = pyglet.graphics.Batch()
    victim_batch = pyglet.graphics.Batch()

    # --- Menu UI Elements ---
    title_label = text.Label('SAR Mission',
                             font_name='Arial', font_size=36,
                             x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 150,
                             anchor_x='center', anchor_y='center')
    start_label = text.Label('Press ENTER to Start',
                             font_name='Arial', font_size=20,
                             x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 50,
                             anchor_x='center', anchor_y='center')
    controls_label = text.Label('Arrows=Move | Z=Toggle Local/Global | +/- or Mouse Wheel=Zoom | ESC=Menu',
                                font_name='Arial', font_size=12,
                                x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 20,
                                anchor_x='center', anchor_y='center')

    # --- View Selection UI ---
    view_select_label = text.Label('Select Starting View',
                                   font_name='Arial', font_size=24,
                                   x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 100,
                                   anchor_x='center', anchor_y='center')
    global_view_label = text.Label('Press G for Global View',
                                   font_name='Arial', font_size=16,
                                   x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 20,
                                   anchor_x='center', anchor_y='center')
    local_view_label = text.Label('Press L for Local View (5x5)',
                                  font_name='Arial', font_size=16,
                                  x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 20,
                                  anchor_x='center', anchor_y='center')

    # --- Difficulty Selection UI ---
    difficulty_title_label = text.Label('Select Difficulty',
                                        font_name='Arial', font_size=24,
                                        x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 100,
                                        anchor_x='center', anchor_y='center')
    easy_label = text.Label('Press E for Easy',
                            font_name='Arial', font_size=16,
                            x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 20,
                            anchor_x='center', anchor_y='center')
    medium_label = text.Label('Press M for Medium',
                              font_name='Arial', font_size=16,
                              x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 20,
                              anchor_x='center', anchor_y='center')
    hard_label = text.Label('Press H for Hard',
                            font_name='Arial', font_size=16,
                            x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 60,
                            anchor_x='center', anchor_y='center')

    # --- Game Over UI ---
    game_over_label = text.Label('Mission Complete!',
                                 font_name='Arial', font_size=32,
                                 x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 50,
                                 anchor_x='center', anchor_y='center')
    time_up_label = text.Label('Time\'s Up!',
                               font_name='Arial', font_size=32,
                               x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 50,
                               anchor_x='center', anchor_y='center')
    restart_label = text.Label('Press ENTER to return to the menu.',
                               font_name='Arial', font_size=16,
                               x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 20,
                               anchor_x='center', anchor_y='center')

    # --- Game Objects ---
    grid_lines = []
    wall_blocks = []
    obstacle_positions = set()
    victims = []
    player = None

    # Victim configuration
    VICTIM_TYPES = {
        'type1': {'color': (255, 255, 0), 'count': 0},  # Yellow
        'type2': {'color': (255, 0, 0),   'count': 0},  # Red
        'type3': {'color': (128, 0, 128), 'count': 0}   # Purple (rare/hard)
    }
    victims_found = {'type1': 0, 'type2': 0, 'type3': 0}

    # --- UI Labels ---
    view_label = text.Label('', font_name='Arial', font_size=14, x=10, y=WINDOW_HEIGHT - 30, batch=ui_batch)
    position_label = text.Label('', font_name='Arial', font_size=12, x=10, y=WINDOW_HEIGHT - 50, batch=ui_batch)
    difficulty_display_label = text.Label('', font_name='Arial', font_size=12, x=10, y=WINDOW_HEIGHT - 70, batch=ui_batch)
    timer_label = text.Label('', font_name='Arial', font_size=14, x=10, y=WINDOW_HEIGHT - 90, batch=ui_batch)
    zoom_label = text.Label('', font_name='Arial', font_size=12, x=10, y=WINDOW_HEIGHT - 110, batch=ui_batch)
    victims_label_type1 = text.Label('', font_name='Arial', font_size=12, x=WINDOW_WIDTH - 150, y=WINDOW_HEIGHT - 30, batch=ui_batch)
    victims_label_type2 = text.Label('', font_name='Arial', font_size=12, x=WINDOW_WIDTH - 150, y=WINDOW_HEIGHT - 50, batch=ui_batch)
    victims_label_type3 = text.Label('', font_name='Arial', font_size=12, x=WINDOW_WIDTH - 150, y=WINDOW_HEIGHT - 70, batch=ui_batch)

    # --- Geometry helpers ---
    def create_shape(points, base_x, base_y):
        shape_coords = set()
        for p in points:
            shape_coords.add((base_x + p[0], base_y + p[1]))
        return list(shape_coords)

    def create_L_shape(x, y, size=4, rotation=0):
        points = []
        for i in range(size): points.append((0, i))
        for i in range(1, size): points.append((i, 0))
        if rotation == 1: points[:] = [(-p[1], p[0]) for p in points]
        elif rotation == 2: points[:] = [(-p[0], -p[1]) for p in points]
        elif rotation == 3: points[:] = [(p[1], -p[0]) for p in points]
        return create_shape(points, x, y)

    def create_U_shape(x, y, width=4, height=3, rotation=0):
        points = []
        for i in range(height): points.extend([(0, i), (width - 1, i)])
        for i in range(width): points.append((i, 0))
        if rotation == 1: points[:] = [(-p[1], p[0]) for p in points]
        elif rotation == 2: points[:] = [(-p[0], -p[1]) for p in points]
        elif rotation == 3: points[:] = [(p[1], -p[0]) for p in points]
        return create_shape(points, x, y)

    def create_T_shape(x, y, width=5, height=3, rotation=0):
        points = []
        mid = width // 2
        for i in range(width): points.append((i, height - 1))
        for i in range(height - 1): points.append((mid, i))
        if rotation == 1: points[:] = [(-p[1], p[0]) for p in points]
        elif rotation == 2: points[:] = [(-p[0], -p[1]) for p in points]
        elif rotation == 3: points[:] = [(p[1], -p[0]) for p in points]
        return create_shape(points, x, y)

    def create_M_shape(x, y, width=5, height=4, rotation=0):
        points = []
        mid = width // 2
        for i in range(height): points.extend([(0, i), (width - 1, i)])
        for i in range(1, mid + 1): points.append((i, height - i))
        for i in range(1, mid): points.append((mid + i, i + 1))
        if rotation == 1: points[:] = [(-p[1], p[0]) for p in points]
        elif rotation == 2: points[:] = [(-p[0], -p[1]) for p in points]
        elif rotation == 3: points[:] = [(p[1], -p[0]) for p in points]
        return create_shape(points, x, y)

    def create_W_shape(x, y, width=5, height=4, rotation=0):
        points = []
        mid = width // 2
        for i in range(height): points.extend([(0, i), (width - 1, i)])
        for i in range(1, mid + 1): points.append((i, i))
        for i in range(1, mid): points.append((mid + i, height - 1 - i))
        if rotation == 1: points[:] = [(-p[1], p[0]) for p in points]
        elif rotation == 2: points[:] = [(-p[0], -p[1]) for p in points]
        elif rotation == 3: points[:] = [(p[1], -p[0]) for p in points]
        return create_shape(points, x, y)

    # --- Pathing / placement helpers ---
    def find_reachable_tiles(start_gx, start_gy):
        q = [(start_gx, start_gy)]
        visited = set([(start_gx, start_gy)])
        while q:
            cx, cy = q.pop(0)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in visited and (nx, ny) not in obstacle_positions:
                    visited.add((nx, ny)); q.append((nx, ny))
        return list(visited)

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def open_neighbors(gx, gy):
        cnt = 0
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            if (gx+dx, gy+dy) not in obstacle_positions:
                cnt += 1
        return cnt

    def is_dead_end(gx, gy):
        if (gx, gy) in obstacle_positions:
            return False
        return open_neighbors(gx, gy) <= 1

    def tile_dist(a, b):
        dx = a[0] - b[0]; dy = a[1] - b[1]
        return (dx*dx + dy*dy) ** 0.5

    def obeys_separation(pos, placed_set, min_sep_overall, min_sep_same, victims_by_pos, this_type):
        for other in placed_set:
            if tile_dist(pos, other) < min_sep_overall:
                return False
        for other in placed_set:
            if victims_by_pos.get(other) == this_type and tile_dist(pos, other) < min_sep_same:
                return False
        return True

    def stratified_regions(total_w, total_h, cols=4, rows=3):
        cell_w = total_w // cols
        cell_h = total_h // rows
        regions = []
        for r in range(rows):
            for c in range(cols):
                x0 = c * cell_w
                y0 = r * cell_h
                x1 = (c+1) * cell_w if c < cols-1 else total_w
                y1 = (r+1) * cell_h if r < rows-1 else total_h
                regions.append(((x0,y0),(x1,y1)))
        return regions

    def cells_in_region(cells, region):
        (x0,y0),(x1,y1) = region
        return [c for c in cells if x0 <= c[0] < x1 and y0 <= c[1] < y1]

    # --- Level generation ---
    def generate_level(selected_difficulty):
        nonlocal obstacle_positions, wall_blocks, victims
        obstacle_positions.clear(); wall_blocks.clear(); victims.clear()

        # Outer boundary walls
        for i in range(TOTAL_GRID_X):
            obstacle_positions.add((i, 0)); obstacle_positions.add((i, TOTAL_GRID_Y - 1))
        for i in range(TOTAL_GRID_Y):
            obstacle_positions.add((0, i)); obstacle_positions.add((TOTAL_GRID_X - 1, i))

        # Walls (kept from your previous config; trimmed comments for brevity)
        wall_configs = {
            'easy': [
                create_L_shape(5, 5, size=5, rotation=0),
                create_L_shape(40, 18, size=4, rotation=2),
                create_L_shape(2, 12, size=6, rotation=1),
                create_U_shape(10, 15, width=7, height=4, rotation=1),
                create_U_shape(25, 2, width=5, height=5, rotation=0),
                create_U_shape(38, 5, width=4, height=6, rotation=3),
                create_T_shape(15, 8, width=5, height=4, rotation=2),
                create_T_shape(30, 20, width=7, height=3, rotation=0),
                create_T_shape(22, 12, width=5, height=5, rotation=1),
                create_M_shape(8, 2, width=5, height=4, rotation=0),
                create_M_shape(33, 15, width=7, height=5, rotation=1),
                create_M_shape(18, 20, width=5, height=4, rotation=2),
                create_W_shape(2, 20, width=5, height=4, rotation=0),
                create_W_shape(40, 2, width=5, height=4, rotation=3),
                create_W_shape(28, 8, width=7, height=4, rotation=0),
                create_W_shape(78, 28, width=4, height=4, rotation=3),
                create_L_shape(72, 32, size=6, rotation=2),
                create_U_shape(75, 36, width=5, height=6, rotation=1),
                create_T_shape(77, 26, width=6, height=4, rotation=0),
                create_M_shape(73, 14, width=5, height=4, rotation=2),
                create_W_shape(71, 20, width=5, height=3, rotation=0),
                create_W_shape(30, 34, width=5, height=4, rotation=3),
                create_L_shape(35, 28, size=5, rotation=0),
                create_U_shape(40, 32, width=6, height=4, rotation=1),
                create_T_shape(45, 36, width=7, height=5, rotation=2),
                create_M_shape(50, 30, width=5, height=4, rotation=0),
                create_W_shape(55, 34, width=4, height=3, rotation=3),
                create_W_shape(48, 12, width=5, height=4, rotation=1),
                create_L_shape(34, 20, size=6, rotation=2),
                create_U_shape(38, 10, width=5, height=5, rotation=0),
                create_T_shape(42, 16, width=6, height=4, rotation=3),
                create_M_shape(46, 14, width=5, height=4, rotation=2),
                create_W_shape(50, 18, width=4, height=4, rotation=0),
                create_U_shape(65, 5,  width=3, height=12, rotation=0),
                create_U_shape(70, 10, width=3, height=15, rotation=0),
                create_U_shape(75, 20, width=2, height=10, rotation=0),
                create_T_shape(61, 8,  width=9,  height=3, rotation=0),
                create_T_shape(66, 16, width=11, height=3, rotation=0),
                create_T_shape(62, 24, width=8,  height=3, rotation=0),
                create_T_shape(68, 30, width=10, height=3, rotation=0),
                create_M_shape(63, 18, width=7, height=4, rotation=0),
                create_W_shape(71, 32, width=6, height=4, rotation=3)
            ],
            'medium': [
                create_L_shape(4, 4, size=7, rotation=1),
                create_L_shape(38, 15, size=5, rotation=2),
                create_L_shape(2, 15, size=6, rotation=2),
                create_L_shape(12, 20, size=5, rotation=3),
                create_U_shape(15, 18, width=6, height=5, rotation=0),
                create_U_shape(25, 2, width=5, height=6, rotation=2),
                create_U_shape(40, 10, width=4, height=6, rotation=3),
                create_U_shape(8, 8, width=7, height=4, rotation=1),
                create_T_shape(30, 5, width=9, height=4, rotation=3),
                create_T_shape(10, 10, width=7, height=4, rotation=0),
                create_T_shape(20, 22, width=9, height=3, rotation=0),
                create_T_shape(35, 2, width=5, height=5, rotation=2),
                create_M_shape(2, 2, width=5, height=4, rotation=0),
                create_M_shape(40, 20, width=5, height=4, rotation=2),
                create_M_shape(25, 15, width=7, height=5, rotation=1),
                create_M_shape(18, 5, width=5, height=4, rotation=3),
                create_W_shape(20, 10, width=7, height=4, rotation=0),
                create_W_shape(33, 18, width=5, height=4, rotation=1),
                create_W_shape(5, 20, width=5, height=4, rotation=0),
                create_W_shape(42, 5, width=3, height=3, rotation=3),
                create_L_shape(72, 8, size=5, rotation=0),
                create_U_shape(74, 12, width=6, height=5, rotation=1),
                create_T_shape(76, 18, width=5, height=4, rotation=2),
                create_M_shape(70, 22, width=5, height=3, rotation=0),
                create_W_shape(78, 28, width=4, height=4, rotation=3),
                create_L_shape(10, 28, size=6, rotation=3),
                create_U_shape(15, 32, width=7, height=5, rotation=0),
                create_T_shape(20, 36, width=8, height=4, rotation=1),
                create_M_shape(25, 30, width=6, height=3, rotation=2),
                create_W_shape(30, 34, width=5, height=4, rotation=3),
                create_L_shape(32, 12, size=5, rotation=1),
                create_U_shape(36, 16, width=6, height=4, rotation=2),
                create_T_shape(40, 14, width=7, height=5, rotation=0),
                create_M_shape(44, 18, width=6, height=3, rotation=3),
                create_W_shape(48, 12, width=5, height=4, rotation=1),
                create_U_shape(65, 5,  width=3, height=12, rotation=0),
                create_U_shape(70, 10, width=3, height=15, rotation=0),
                create_U_shape(75, 20, width=2, height=10, rotation=0),
                create_T_shape(62, 8,  width=10, height=3, rotation=0),
                create_T_shape(66, 18, width=12, height=3, rotation=0),
                create_T_shape(68, 28, width=14, height=3, rotation=0),
                create_W_shape(50, 18, width=4, height=4, rotation=0),
                create_T_shape(61, 8,  width=9,  height=3, rotation=0),
                create_T_shape(66, 16, width=11, height=2, rotation=0),
                create_T_shape(62, 24, width=8,  height=3, rotation=0),
                create_T_shape(68, 30, width=10, height=6, rotation=0),
                create_M_shape(63, 18, width=7, height=4, rotation=0),
                create_W_shape(71, 32, width=6, height=4, rotation=3)
            ],
            'hard': [
                create_L_shape(3, 3, size=8, rotation=0),
                create_L_shape(35, 2, size=6, rotation=3),
                create_L_shape(40, 20, size=4, rotation=2),
                create_L_shape(18, 2, size=7, rotation=1),
                create_L_shape(42, 8, size=5, rotation=0),
                create_L_shape(10, 18, size=6, rotation=2),
                create_L_shape(2, 22, size=4, rotation=1),
                create_U_shape(12, 12, width=5, height=8, rotation=1),
                create_U_shape(20, 5, width=7, height=4, rotation=2),
                create_U_shape(30, 12, width=6, height=6, rotation=0),
                create_U_shape(2, 8, width=4, height=7, rotation=3),
                create_U_shape(42, 2, width=3, height=5, rotation=2),
                create_U_shape(25, 22, width=8, height=3, rotation=0),
                create_T_shape(25, 18, width=10, height=5, rotation=0),
                create_T_shape(8, 20, width=6, height=4, rotation=1),
                create_T_shape(2, 10, width=8, height=5, rotation=3),
                create_T_shape(38, 8, width=5, height=6, rotation=2),
                create_T_shape(15, 2, width=7, height=4, rotation=0),
                create_T_shape(28, 5, width=5, height=5, rotation=1),
                create_M_shape(6, 2, width=5, height=4, rotation=0),
                create_M_shape(40, 15, width=5, height=5, rotation=2),
                create_M_shape(15, 22, width=7, height=3, rotation=0),
                create_M_shape(33, 20, width=5, height=4, rotation=1),
                create_M_shape(22, 2, width=5, height=4, rotation=3),
                create_W_shape(2, 15, width=5, height=4, rotation=0),
                create_W_shape(42, 18, width=3, height=3, rotation=2),
                create_W_shape(30, 2, width=7, height=4, rotation=0),
                create_W_shape(20, 15, width=5, height=5, rotation=1),
                create_W_shape(8, 8, width=5, height=4, rotation=3),
                create_W_shape(35, 15, width=5, height=4, rotation=0),
                create_T_shape(22, 12, width=7, height=4, rotation=0),
                create_L_shape(25, 15, size=5, rotation=3),
                create_U_shape(18, 10, width=5, height=4, rotation=2),
                create_T_shape(45, 22, width=7, height=4, rotation=1),
                create_L_shape(50, 5, size=6, rotation=0),
                create_U_shape(55, 10, width=6, height=5, rotation=2),
                create_M_shape(60, 12, width=5, height=4, rotation=1),
                create_W_shape(65, 18, width=5, height=4, rotation=0),
                create_L_shape(70, 6, size=5, rotation=2),
                create_T_shape(72, 24, width=6, height=4, rotation=3),
                create_U_shape(48, 28, width=5, height=5, rotation=0),
                create_M_shape(52, 30, width=6, height=3, rotation=2),
                create_W_shape(58, 32, width=4, height=3, rotation=1),
                create_L_shape(62, 26, size=4, rotation=3),
                create_T_shape(68, 14, width=8, height=4, rotation=0),
                create_U_shape(74, 20, width=4, height=6, rotation=1),
                create_M_shape(76, 8, width=5, height=4, rotation=0),
                create_W_shape(44, 34, width=6, height=3, rotation=2),
                create_L_shape(28, 28, size=6, rotation=1),
                create_T_shape(10, 26, width=7, height=4, rotation=2),
                create_L_shape(12, 28, size=5, rotation=0),
                create_U_shape(18, 30, width=6, height=4, rotation=2),
                create_T_shape(24, 32, width=7, height=4, rotation=1),
                create_M_shape(30, 34, width=5, height=4, rotation=3),
                create_W_shape(36, 36, width=6, height=3, rotation=0),
                create_L_shape(42, 30, size=6, rotation=2),
                create_U_shape(48, 24, width=5, height=5, rotation=1),
                create_T_shape(54, 18, width=8, height=4, rotation=0),
                create_M_shape(60, 12, width=5, height=3, rotation=2),
                create_W_shape(66, 6, width=4, height=4, rotation=3),
                create_L_shape(72, 5, size=6, rotation=1),
                create_U_shape(74, 10, width=5, height=6, rotation=0),
                create_T_shape(76, 15, width=6, height=4, rotation=2),
                create_M_shape(70, 20, width=5, height=4, rotation=3),
                create_W_shape(78, 25, width=4, height=4, rotation=1),
                create_T_shape(61, 8,  width=9,  height=3, rotation=0),
                create_T_shape(66, 16, width=11, height=3, rotation=0),
                create_T_shape(62, 24, width=8,  height=3, rotation=0),
                create_T_shape(68, 30, width=10, height=3, rotation=0)
            ]
        }

        for wall_shape in wall_configs[selected_difficulty]:
            for pos in wall_shape:
                if 0 < pos[0] < TOTAL_GRID_X - 1 and 0 < pos[1] < TOTAL_GRID_Y - 1:
                    obstacle_positions.add(pos)

        # Draw wall blocks
        for x, y in obstacle_positions:
            wall_blocks.append(shapes.Rectangle(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE,
                                                color=(169, 169, 169), batch=batch))

        # Start position
        player_start_gx, player_start_gy = 0, 0
        while True:
            px, py = random.randint(1, TOTAL_GRID_X - 2), random.randint(1, TOTAL_GRID_Y - 2)
            if (px, py) not in obstacle_positions:
                player_start_gx, player_start_gy = px, py
                break

        reachable_tiles = find_reachable_tiles(player_start_gx, player_start_gy)

        # --- Victim counts (fewer purples) ---
        victim_counts = {
            'easy':   {'type1': 60, 'type2': 60, 'type3': 20},
            'medium': {'type1': 60, 'type2': 60, 'type3': 15},
            'hard':   {'type1': 60, 'type2': 60, 'type3': 10}
        }
        for t in ('type1', 'type2', 'type3'):
            VICTIM_TYPES[t]['count'] = victim_counts[selected_difficulty][t]

        # --- Placement with special rules & dispersion ---
        placed_victim_positions = set()
        victims_by_pos = {}  # (gx,gy) -> type
        start_cell = (player_start_gx, player_start_gy)

        # Separation parameters (in tiles)
        MIN_SEP_OVERALL = 6    # min distance between any two victims
        MIN_SEP_SAME    = 8    # extra spacing for same-type

        # PURPLE (type3): dead-ends far away; place first
        def hard_candidates(min_dist=30):
            return [cell for cell in reachable_tiles
                    if cell != start_cell
                    and cell not in placed_victim_positions
                    and is_dead_end(*cell)
                    and manhattan(cell, start_cell) >= min_dist]

        purple_needed = VICTIM_TYPES['type3']['count']
        purple_color = VICTIM_TYPES['type3']['color']
        candidates = hard_candidates(min_dist=30)
        random.shuffle(candidates)

        if len(candidates) < purple_needed:
            relaxed = [c for c in reachable_tiles
                       if c != start_cell
                       and c not in placed_victim_positions
                       and is_dead_end(*c)
                       and manhattan(c, start_cell) >= 15]
            random.shuffle(relaxed)
            seen = set(candidates)
            for c in relaxed:
                if c not in seen:
                    candidates.append(c); seen.add(c)
        if len(candidates) < purple_needed:
            fallback = [c for c in reachable_tiles if c != start_cell and c not in placed_victim_positions]
            fallback.sort(key=lambda c: manhattan(c, start_cell), reverse=True)
            for c in fallback:
                if c not in candidates:
                    candidates.append(c)

        # Enforce separation among purples
        chosen = []
        for cell in candidates:
            if len(chosen) >= purple_needed: break
            if all(tile_dist(cell, other) >= MIN_SEP_SAME for other in chosen):
                chosen.append(cell)
        if len(chosen) < purple_needed:
            for cell in candidates:
                if len(chosen) >= purple_needed: break
                if all(tile_dist(cell, other) >= max(4, MIN_SEP_SAME-2) for other in chosen):
                    chosen.append(cell)
        if len(chosen) < purple_needed:
            for cell in candidates:
                if len(chosen) >= purple_needed: break
                if all(tile_dist(cell, other) >= max(3, MIN_SEP_OVERALL-3) for other in chosen):
                    chosen.append(cell)

        for vx, vy in chosen[:purple_needed]:
            placed_victim_positions.add((vx, vy))
            victims_by_pos[(vx, vy)] = 'type3'
            victim_shape = shapes.Triangle(
                vx * CELL_SIZE + CELL_SIZE / 2, vy * CELL_SIZE + CELL_SIZE - 5,
                vx * CELL_SIZE + 5,           vy * CELL_SIZE + 5,
                vx * CELL_SIZE + CELL_SIZE - 5, vy * CELL_SIZE + 5,
                color=purple_color, batch=victim_batch
            )
            victims.append({'gx': vx, 'gy': vy, 'type': 'type3', 'shape': victim_shape})

        # YELLOW/RED (type1/type2): stratified across regions with separation
        regions = stratified_regions(TOTAL_GRID_X, TOTAL_GRID_Y, cols=4, rows=3)

        # Build per-region pools (reachable & not occupied)
        region_pools = []
        for reg in regions:
            cells = [(gx, gy) for (gx, gy) in cells_in_region(reachable_tiles, reg)
                     if (gx, gy) != start_cell and (gx, gy) not in placed_victim_positions]
            random.shuffle(cells)
            region_pools.append(cells)

        def distribute_counts_evenly(total, buckets):
            base = total // buckets
            rem = total % buckets
            dist = [base] * buckets
            order = list(range(buckets))
            random.shuffle(order)
            for i in range(rem):
                dist[order[i]] += 1
            return dist

        for v_type in ['type2', 'type1']:  # red first, then yellow
            need = VICTIM_TYPES[v_type]['count']
            color = VICTIM_TYPES[v_type]['color']
            per_region = distribute_counts_evenly(need, len(regions))

            for idx, want in enumerate(per_region):
                if want <= 0: continue
                pool = region_pools[idx]
                # attempts with gradually relaxed separation
                attempts_sep = [(MIN_SEP_OVERALL, MIN_SEP_SAME),
                                (max(4, MIN_SEP_OVERALL-1), max(6, MIN_SEP_SAME-1)),
                                (max(3, MIN_SEP_OVERALL-2), max(5, MIN_SEP_SAME-2))]
                placed_here = 0
                for (sep_all, sep_same) in attempts_sep:
                    if placed_here >= want: break
                    random.shuffle(pool)
                    for cell in list(pool):
                        if placed_here >= want: break
                        if cell in placed_victim_positions:
                            continue
                        if obeys_separation(cell, placed_victim_positions, sep_all, sep_same, victims_by_pos, v_type):
                            vx, vy = cell
                            placed_victim_positions.add(cell)
                            victims_by_pos[cell] = v_type
                            victim_shape = shapes.Triangle(
                                vx * CELL_SIZE + CELL_SIZE / 2, vy * CELL_SIZE + CELL_SIZE - 5,
                                vx * CELL_SIZE + 5,           vy * CELL_SIZE + 5,
                                vx * CELL_SIZE + CELL_SIZE - 5, vy * CELL_SIZE + 5,
                                color=color, batch=victim_batch
                            )
                            victims.append({'gx': vx, 'gy': vy, 'type': v_type, 'shape': victim_shape})
                            placed_here += 1
                per_region[idx] = want - placed_here  # leftover for this region

            # Spillover anywhere, still enforce separation
            leftovers = sum(per_region)
            if leftovers > 0:
                global_pool = [c for c in reachable_tiles if c != start_cell and c not in placed_victim_positions]
                global_pool.sort(key=lambda c: manhattan(c, start_cell), reverse=True)
                attempts_sep = [(MIN_SEP_OVERALL, MIN_SEP_SAME),
                                (max(4, MIN_SEP_OVERALL-1), max(6, MIN_SEP_SAME-1)),
                                (max(3, MIN_SEP_OVERALL-2), max(5, MIN_SEP_SAME-2))]
                placed_cnt = 0
                for (sep_all, sep_same) in attempts_sep:
                    if placed_cnt >= leftovers: break
                    for cell in list(global_pool):
                        if placed_cnt >= leftovers: break
                        if cell in placed_victim_positions:
                            continue
                        if obeys_separation(cell, placed_victim_positions, sep_all, sep_same, victims_by_pos, v_type):
                            vx, vy = cell
                            placed_victim_positions.add(cell)
                            victims_by_pos[cell] = v_type
                            victim_shape = shapes.Triangle(
                                vx * CELL_SIZE + CELL_SIZE / 2, vy * CELL_SIZE + CELL_SIZE - 5,
                                vx * CELL_SIZE + 5,           vy * CELL_SIZE + 5,
                                vx * CELL_SIZE + CELL_SIZE - 5, vy * CELL_SIZE + 5,
                                color=color, batch=victim_batch
                            )
                            victims.append({'gx': vx, 'gy': vy, 'type': v_type, 'shape': victim_shape})
                            placed_cnt += 1

        return (player_start_gx * CELL_SIZE + CELL_SIZE // 2,
                player_start_gy * CELL_SIZE + CELL_SIZE // 2)

    # --- Game setup / state updates ---
    def setup_game(selected_difficulty):
        nonlocal player, difficulty, time_remaining, current_zoom, zoom_level
        difficulty = selected_difficulty
        current_zoom = selected_initial_view
        zoom_level = 1.0  # reset zoom each game

        if player: player.delete(); player = None
        for wb in wall_blocks: wb.delete()
        for v in victims: v['shape'].delete()

        player_start_x, player_start_y = generate_level(difficulty)
        player = shapes.Circle(player_start_x, player_start_y, CELL_SIZE // 2 - 5, color=(0, 255, 0), batch=batch)

        for v_type in victims_found: victims_found[v_type] = 0
        time_remaining = TIME_LIMIT
        pyglet.clock.schedule_interval(update, 1/60.0)
        update_ui_labels()

    def is_obstacle(x, y):
        gx, gy = x // CELL_SIZE, y // CELL_SIZE
        return (gx, gy) in obstacle_positions

    def update_ui_labels():
        if game_state == "playing":
            view_label.text = f"View: {current_zoom.upper()} (Z)"
            gx, gy = player.x // CELL_SIZE, player.y // CELL_SIZE
            position_label.text = f"Pos: ({gx}, {gy})"
            difficulty_display_label.text = f"Difficulty: {difficulty.capitalize()}"
            zoom_label.text = f"Zoom: {int(zoom_level*100)}%"
            victims_label_type1.text = f"Yellow: {victims_found['type1']} / {VICTIM_TYPES['type1']['count']}"
            victims_label_type2.text = f"Red: {victims_found['type2']} / {VICTIM_TYPES['type2']['count']}"
            victims_label_type3.text = f"Purple: {victims_found['type3']} / {VICTIM_TYPES['type3']['count']}"

    def update(dt):
        nonlocal time_remaining, game_state
        if game_state == "playing":
            time_remaining -= dt
            if time_remaining < 0: time_remaining = 0
            mins, secs = divmod(time_remaining, 60)
            timer_label.text = f"Time: {int(mins):02d}:{int(secs):02d}"
            if time_remaining <= 0:
                game_state = "game_over_time"
                pyglet.clock.unschedule(update)

    def check_for_victim():
        nonlocal game_state
        player_gx, player_gy = player.x // CELL_SIZE, player.y // CELL_SIZE
        victim_to_remove = None
        for victim in victims:
            if victim['gx'] == player_gx and victim['gy'] == player_gy:
                victims_found[victim['type']] += 1
                victim['shape'].delete()
                victim_to_remove = victim
                break
        if victim_to_remove:
            victims.remove(victim_to_remove)
            update_ui_labels()

        total_victims = sum(data['count'] for data in VICTIM_TYPES.values())
        total_found = sum(victims_found.values())
        if total_found > 0 and total_found >= total_victims:
            game_state = "game_over"
            pyglet.clock.unschedule(update)

    # --- Projection helpers ---
    def set_projection(center_x, center_y, view_w, view_h):
        left   = max(0, min(WINDOW_WIDTH  - view_w, center_x - view_w / 2))
        bottom = max(0, min(WINDOW_HEIGHT - view_h, center_y - view_h / 2))
        right  = left + view_w
        top    = bottom + view_h
        window.viewport = (0, 0, window.width, window.height)
        window.projection = pyglet.math.Mat4.orthogonal_projection(left, right, bottom, top, -1, 1)

    # --- Events ---
    @window.event
    def on_draw():
        window.clear()
        if game_state == "menu":
            title_label.draw(); start_label.draw(); controls_label.draw()
        elif game_state == "view_select":
            view_select_label.draw(); global_view_label.draw(); local_view_label.draw()
        elif game_state == "difficulty_select":
            difficulty_title_label.draw(); easy_label.draw(); medium_label.draw(); hard_label.draw()
        elif game_state == "playing":
            if current_zoom == "global":
                vw = WINDOW_WIDTH  / zoom_level
                vh = WINDOW_HEIGHT / zoom_level
            else:  # local view (base 5x5 tiles)
                base = 5 * CELL_SIZE
                vw = base / zoom_level
                vh = base / zoom_level

            cx = player.x if player else WINDOW_WIDTH/2
            cy = player.y if player else WINDOW_HEIGHT/2
            set_projection(cx, cy, vw, vh)

            batch.draw()
            victim_batch.draw()

            # UI overlay
            window.viewport = (0, 0, window.width, window.height)
            window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
            ui_batch.draw()
        elif game_state == "game_over":
            game_over_label.draw(); restart_label.draw()
        elif game_state == "game_over_time":
            time_up_label.draw(); restart_label.draw()

    @window.event
    def on_key_press(symbol, modifiers):
        nonlocal game_state, current_zoom, selected_initial_view, zoom_level
        if game_state == "menu":
            if symbol == key.ENTER: game_state = "view_select"
        elif game_state == "view_select":
            if symbol == key.G: selected_initial_view = "global"; game_state = "difficulty_select"
            elif symbol == key.L: selected_initial_view = "local"; game_state = "difficulty_select"
            elif symbol == key.ESCAPE: game_state = "menu"
        elif game_state == "difficulty_select":
            if symbol == key.E: setup_game('easy'); game_state = "playing"
            elif symbol == key.M: setup_game('medium'); game_state = "playing"
            elif symbol == key.H: setup_game('hard'); game_state = "playing"
            elif symbol == key.ESCAPE: game_state = "view_select"
        elif game_state == "playing":
            if symbol == key.Z:
                current_zoom = "local" if current_zoom == "global" else "global"
                update_ui_labels(); return
            # Zoom keys
            if symbol in (key.NUM_ADD, key.PLUS, key.EQUAL):
                zoom_level = min(MAX_ZOOM, round(zoom_level * 1.10, 4)); update_ui_labels(); return
            if symbol in (key.NUM_SUBTRACT, key.MINUS):
                zoom_level = max(MIN_ZOOM, round(zoom_level / 1.10, 4)); update_ui_labels(); return
            # ESC back
            if symbol == key.ESCAPE:
                game_state = "menu"; pyglet.clock.unschedule(update); return
            # Movement (grid step)
            new_x, new_y = player.x, player.y
            if symbol == key.RIGHT: new_x += CELL_SIZE
            elif symbol == key.LEFT: new_x -= CELL_SIZE
            elif symbol == key.UP: new_y += CELL_SIZE
            elif symbol == key.DOWN: new_y -= CELL_SIZE
            if not is_obstacle(new_x, new_y):
                player.x = new_x; player.y = new_y
                check_for_victim(); update_ui_labels()
        elif game_state in ("game_over", "game_over_time"):
            if symbol == key.ENTER: game_state = "menu"

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        nonlocal zoom_level
        if game_state != "playing": return
        factor = 1.10 if scroll_y > 0 else (1 / 1.10)
        zoom_level = max(MIN_ZOOM, min(MAX_ZOOM, round(zoom_level * factor, 4)))
        update_ui_labels()

    # Initial grid lines (drawn once)
    for i in range(TOTAL_GRID_X + 1):
        x = i * CELL_SIZE
        grid_lines.append(shapes.Line(x, 0, x, WINDOW_HEIGHT, color=(50, 50, 50), batch=batch))
    for i in range(TOTAL_GRID_Y + 1):
        y = i * CELL_SIZE
        grid_lines.append(shapes.Line(0, y, WINDOW_WIDTH, y, color=(50, 50, 50), batch=batch))

    pyglet.app.run()

if __name__ == "__main__":
    run_sar_mission_game()
