import pyglet
from pyglet import shapes, text
from pyglet.window import key


def run_sar_mission_game():
    WINDOW_SIZE = 600
    CELL_SIZE = 40
    TOTAL_GRID = WINDOW_SIZE // CELL_SIZE

    window = pyglet.window.Window(WINDOW_SIZE, WINDOW_SIZE, "SAR Mission")
    
    # Game states
    game_state = "menu"  # "menu", "playing"
    selected_view = None  # Will be "global" or "local"
    current_zoom = "global"
    
    batch = pyglet.graphics.Batch()
    ui_batch = pyglet.graphics.Batch()

    # === Menu Elements ===
    title_label = text.Label('SAR Mission - Choose Your View', 
                            font_name='Arial', font_size=24,
                            x=WINDOW_SIZE//2, y=WINDOW_SIZE//2 + 100,
                            anchor_x='center', anchor_y='center')
    
    global_label = text.Label('Press G for GLOBAL view (see entire map)', 
                             font_name='Arial', font_size=16,
                             x=WINDOW_SIZE//2, y=WINDOW_SIZE//2 + 20,
                             anchor_x='center', anchor_y='center')
    
    local_label = text.Label('Press L for LOCAL view (zoomed in)', 
                            font_name='Arial', font_size=16,
                            x=WINDOW_SIZE//2, y=WINDOW_SIZE//2 - 20,
                            anchor_x='center', anchor_y='center')
    
    controls_label = text.Label('Use Z to toggle views during game | Arrow keys to move', 
                               font_name='Arial', font_size=12,
                               x=WINDOW_SIZE//2, y=WINDOW_SIZE//2 - 80,
                               anchor_x='center', anchor_y='center')

    # === Grid Lines ===
    grid_lines = []
    # Vertical lines
    for i in range(TOTAL_GRID + 1):
        x = i * CELL_SIZE
        grid_lines.append(shapes.Line(x, 0, x, WINDOW_SIZE, color=(200, 200, 200), batch=batch))
    
    # Horizontal lines
    for i in range(TOTAL_GRID + 1):
        y = i * CELL_SIZE
        grid_lines.append(shapes.Line(0, y, WINDOW_SIZE, y, color=(200, 200, 200), batch=batch))

    # === Obstacles ===
    wall1 = [(x, y) for x in range(3, 5) for y in range(3, 4)]
    wall2 = [(x, y) for x in range(5, 7) for y in range(6, 8)]
    wall3 = [(x, y) for x in range(1, 5) for y in range(9, 11)]
    wall4 = [(x, y) for x in range(8, 9) for y in range(2, 5)]
    wall5 = [(x, y) for x in range(9, 10) for y in range(5, 6)]
    wall6 = [(x, y) for x in range(3, 4) for y in range(8, 12)]

    obstacle_positions = wall1 + wall2 + wall3 + wall4 + wall5 + wall6

    # === Wall blocks ===
    wall_blocks = []
    for i in range(TOTAL_GRID):
        wall_blocks.append(shapes.Rectangle(i * CELL_SIZE, 0, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))
        wall_blocks.append(shapes.Rectangle(i * CELL_SIZE, WINDOW_SIZE - CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))
        wall_blocks.append(shapes.Rectangle(0, i * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))
        wall_blocks.append(shapes.Rectangle(WINDOW_SIZE - CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(125, 0, 125), batch=batch))

    for x, y in obstacle_positions:
        wall_blocks.append(shapes.Rectangle(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(169, 169, 169), batch=batch))

    # === Player ===
    player_x = WINDOW_SIZE // 2
    player_y = WINDOW_SIZE // 2
    circle = shapes.Circle(player_x, player_y, CELL_SIZE // 2 - 5, color=(255, 0, 0), batch=batch)

    # === Game UI Labels ===
    view_label = text.Label('', font_name='Arial', font_size=14,
                           x=10, y=WINDOW_SIZE - 30, batch=ui_batch)
    
    position_label = text.Label('', font_name='Arial', font_size=12,
                               x=10, y=WINDOW_SIZE - 50, batch=ui_batch)

    def is_obstacle(x, y):
        gx, gy = x // CELL_SIZE, y // CELL_SIZE
        # Check boundaries - don't allow movement into border walls
        if gx < 1 or gx >= TOTAL_GRID - 1 or gy < 1 or gy >= TOTAL_GRID - 1:
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
            # Draw menu
            window.viewport = (0, 0, window.width, window.height)
            window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_SIZE, 0, WINDOW_SIZE, -1, 1)
            title_label.draw()
            global_label.draw()
            local_label.draw()
            controls_label.draw()
        
        elif game_state == "playing":
            # Set up projection based on current zoom
            if current_zoom == "global":
                # Global view - see entire map
                window.viewport = (0, 0, window.width, window.height)
                window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_SIZE, 0, WINDOW_SIZE, -1, 1)
            else:
                # Local view - zoomed in around player
                zoom_size = WINDOW_SIZE // 3  # More zoomed in than before
                left = max(0, min(WINDOW_SIZE - zoom_size, player_x - zoom_size // 2))
                right = left + zoom_size
                bottom = max(0, min(WINDOW_SIZE - zoom_size, player_y - zoom_size // 2))
                top = bottom + zoom_size
                
                window.viewport = (0, 0, window.width, window.height)
                window.projection = pyglet.math.Mat4.orthogonal_projection(left, right, bottom, top, -1, 1)

            # Draw game elements
            batch.draw()
            
            # Draw UI elements (always in screen space)
            window.viewport = (0, 0, window.width, window.height)
            window.projection = pyglet.math.Mat4.orthogonal_projection(0, WINDOW_SIZE, 0, WINDOW_SIZE, -1, 1)
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
                # Toggle between views
                current_zoom = "local" if current_zoom == "global" else "global"
                update_ui_labels()
                return
            
            if symbol == key.ESCAPE:
                # Return to menu
                game_state = "menu"
                return

            # Player movement
            new_x, new_y = player_x, player_y
            if symbol == key.RIGHT: 
                new_x += CELL_SIZE
            elif symbol == key.LEFT: 
                new_x -= CELL_SIZE
            elif symbol == key.UP: 
                new_y += CELL_SIZE
            elif symbol == key.DOWN: 
                new_y -= CELL_SIZE

            if not is_obstacle(new_x, new_y):
                player_x = new_x
                player_y = new_y
                circle.x = player_x
                circle.y = player_y
                update_ui_labels()

    pyglet.app.run()

if __name__ == "__main__":
    run_sar_mission_game()