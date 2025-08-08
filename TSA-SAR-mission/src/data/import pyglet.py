import pyglet
from pyglet import shapes, text
from pyglet.window import key


def run_sar_mission_game():
    
    WINDOW_WIDTH = 1800
    WINDOW_HEIGHT = 1000
    CELL_SIZE = 40
    TOTAL_GRID_X = WINDOW_WIDTH // CELL_SIZE
    TOTAL_GRID_Y = WINDOW_HEIGHT // CELL_SIZE

    window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Mission")
    game_state = "menu"
    selected_view = None
    current_zoom = "global"

    batch = pyglet.graphics.Batch()
    ui_batch = pyglet.graphics.Batch()

    # Menu Labels
    title_label = text.Label('SAR Mission - Choose Your View',
                             font_name='Arial', font_size=24,
                             x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 100,
                             anchor_x='center', anchor_y='center')
    global_label = text.Label('Press G for GLOBAL view (see entire map)',
                              font_name='Arial', font_size=16,
                              x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 + 20,
                              anchor_x='center', anchor_y='center')
    local_label = text.Label('Press L for LOCAL view (zoomed in)',
                             font_name='Arial', font_size=16,
                             x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 20,
                             anchor_x='center', anchor_y='center')
    controls_label = text.Label('Use Z to toggle views during game | Arrow keys to move',
                                font_name='Arial', font_size=12,
                                x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2 - 80,
                                anchor_x='center', anchor_y='center')

    # Grid lines
    grid_lines = []
    for i in range(TOTAL_GRID_X + 1):
        x = i * CELL_SIZE
        grid_lines.append(shapes.Line(x, 0, x, WINDOW_HEIGHT, color=(80, 80, 80), batch=batch))
    for i in range(TOTAL_GRID_Y + 1):
        y = i * CELL_SIZE
        grid_lines.append(shapes.Line(0, y, WINDOW_WIDTH, y, color=(80, 80, 80), batch=batch))

    # Obstacles
    wall1 = [(x, y) for x in range(23, 25) for y in range(13,18)]
    wall2 = [(x, y) for x in range(5, 7) for y in range(6, 8)]
    wall3 = [(x, y) for x in range(1, 5) for y in range(9, 11)]
    wall4 = [(x, y) for x in range(8, 9) for y in range(2, 5)]
    wall5 = [(36, y) for y in range(2, 6)]
    wall6 = [(x, 3) for x in range(36, 40)]
    wall7 = [(x, y) for x in range(21, 24) for y in range(3, 4)]
    wall8 = [(x, y) for x in range(5, 7) for y in range(6, 8)]
    wall9 = [(x, y) for x in range(22, 27) for y in range(14, 20)]
    wall10 = [(x, 2) for x in range(5, 24)]
    wall11 = [(x, y) for x in range(17, 20) for y in range(5, 6)]
    wall12 = [(x, y) for x in range(11, 17) for y in range(8, 10)]
    wall13 = [(x, 4) for x in range(1, 21)]
    wall14 = [(24, y) for y in range(9, 20)]
    wall15 = [(x, 6) for x in range(3, 12)]
    wall16 = [(x, 7) for x in range(13, 19)]
    wall17 = [(x, 18) for x in range(17, 24)]
    wall18 = [(x, 14) for x in range(14, 18)]
    wall19 = [(x, 7) for x in range(9, 14)]
    wall20 = [(37, y) for y in range(11, 18)]

    obstacle_positions = (
        wall1 + wall2 + wall3 + wall4 + wall5 + wall6 + wall7 + wall8 +
        wall9 + wall10 + wall11 + wall12 +
        wall13 + wall14 + wall15 + wall16 + wall17 + wall18 + wall19 + wall20
    )

    wall_blocks = []
    for i in range(TOTAL_GRID_X):
        wall_blocks.append(shapes.Rectangle(i * CELL_SIZE, 0, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))
        wall_blocks.append(shapes.Rectangle(i * CELL_SIZE, WINDOW_HEIGHT - CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))
    for i in range(TOTAL_GRID_Y):
        wall_blocks.append(shapes.Rectangle(0, i * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))
        wall_blocks.append(shapes.Rectangle(WINDOW_WIDTH - CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))

    for x, y in obstacle_positions:
        wall_blocks.append(shapes.Rectangle(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(169, 169, 169), batch=batch))

    # Player
    player_x = WINDOW_WIDTH // 2
    player_y = WINDOW_HEIGHT // 2
    circle = shapes.Circle(player_x, player_y, CELL_SIZE // 2 - 5, color=(255, 0, 0), batch=batch)

    # UI
    view_label = text.Label('', font_name='Arial', font_size=14, x=10, y=WINDOW_HEIGHT - 30, batch=ui_batch)
    position_label = text.Label('', font_name='Arial', font_size=12, x=10, y=WINDOW_HEIGHT - 50, batch=ui_batch)

    def is_obstacle(x, y):
        gx, gy = x // CELL_SIZE, y // CELL_SIZE
        if gx < 1 or gx >= TOTAL_GRID_X - 1 or gy < 1 or gy >= TOTAL_GRID_Y - 1:
            return True
        return (gx, gy) in obstacle_positions

    def update_ui_labels():
        if game_state == "playing":
            view_label.text = f"Current View: {current_zoom.upper()} (Press Z to toggle)"
            gx, gy = player_x // CELL_SIZE, player_y // CELL_SIZE
            position_label.text = f"Position: Grid ({gx}, {gy})"

    @window.event
    def on_draw():
        window.clear()
        if game_state == "menu":
            window.viewport = (0, 0, window.width, window.height)
            window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
            title_label.draw()
            global_label.draw()
            local_label.draw()
            controls_label.draw()
        elif game_state == "playing":
            if current_zoom == "global":
                window.viewport = (0, 0, window.width, window.height)
                window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
            else:
                zoom_w = WINDOW_WIDTH // 3
                zoom_h = WINDOW_HEIGHT // 3
                left = max(0, min(WINDOW_WIDTH - zoom_w, player_x - zoom_w // 2))
                right = left + zoom_w
                bottom = max(0, min(WINDOW_HEIGHT - zoom_h, player_y - zoom_h // 2))
                top = bottom + zoom_h
                window.viewport = (0, 0, window.width, window.height)
                window.projection = pyglet.math.Mat4.orthogonal_projection(left, right, bottom, top, -1, 1)

            batch.draw()

            # UI (always full screen)
            window.viewport = (0, 0, window.width, window.height)
            window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
            ui_batch.draw()

    @window.event
    def on_key_press(symbol, modifiers):
        nonlocal game_state, selected_view, current_zoom, player_x, player_y

        if game_state == "menu":
            if symbol == key.G:
                selected_view = "global"
                current_zoom = "global"
                game_state = "playing"
                update_ui_labels()
            elif symbol == key.L:
                selected_view = "local"
                current_zoom = "local"
                game_state = "playing"
                update_ui_labels()

        elif game_state == "playing":
            if symbol == key.Z:
                current_zoom = "local" if current_zoom == "global" else "global"
                update_ui_labels()
                return
            if symbol == key.ESCAPE:
                game_state = "menu"
                return

            # Player movement
            new_x, new_y = player_x, player_y
            if symbol == key.RIGHT: new_x += CELL_SIZE
            elif symbol == key.LEFT: new_x -= CELL_SIZE
            elif symbol == key.UP: new_y += CELL_SIZE
            elif symbol == key.DOWN: new_y -= CELL_SIZE

            if not is_obstacle(new_x, new_y):
                player_x = new_x
                player_y = new_y
                circle.x = player_x
                circle.y = player_y
                update_ui_labels()

    pyglet.app.run()


if __name__ == "__main__":
    run_sar_mission_game()
