import numpy as np
import pyglet
from pyglet import shapes
from pyglet.window import key

from .camera import Camera
from .walls import GridWorldGenerator


# Main Game Class
class MainGUI(pyglet.window.Window):
    def __init__(self, width, height, config, grid_array=None):
        super().__init__(width, height, caption="Grid World with Wall Shapes")

        self.CELL_SIZE = config["CELL_SIZE"]  # Size of each cell in the grid
        self.GRID_WIDTH = config["WIDTH"] // self.CELL_SIZE  # Number of columns
        self.GRID_HEIGHT = config["HEIGHT"] // self.CELL_SIZE  # Number of rows

        # Handle keys
        self.keys = key.KeyStateHandler()

        # Generate the grid with walls
        grid_generator = GridWorldGenerator(self.GRID_WIDTH, self.GRID_HEIGHT)
        grid_generator.generate_walls()
        if grid_array is None:
            self.grid_array = grid_generator.get_grid()
        else:
            self.grid_array = grid_array

        # print(self.grid_array)
        # print(self.grid_array.shape)

        # Place the player in the center of the grid
        self.grid_array[self.GRID_HEIGHT // 2, self.GRID_WIDTH // 2] = (
            2  # Player starts at the center
        )

        # Apply the scaling to the window's view matrix
        self.camera = Camera(self.width, self.height, zoom=config["ZOOM_LEVEL"])
        self.change_zoom()

        # Create a batch for efficient drawing
        self.batch = pyglet.graphics.Batch()
        self.shapes = []  # To store all shapes
        self.player_shapes = []  # To store player shapes separately
        self.draw_grid()
        self.draw_player()

    def change_zoom(self):
        player_pos = np.argwhere(self.grid_array == 2)[0]
        player_x = player_pos[1] * self.CELL_SIZE
        player_y = player_pos[0] * self.CELL_SIZE
        self.camera.center_player(player_x, player_y)
        self.view = self.camera.get_view_matrix()

    def follow_player(self):
        player_pos = np.argwhere(self.grid_array == 2)[0]
        player_x = player_pos[1] * self.CELL_SIZE + self.CELL_SIZE / 2
        player_y = player_pos[0] * self.CELL_SIZE + self.CELL_SIZE / 2
        self.camera.keep_target_in_view(player_x, player_y)
        self.view = self.camera.get_view_matrix()

    def draw_grid(self):
        """Draw the grid with walls, roads, buildings, debris, and player."""
        self.shapes.clear()  # Clear previous shapes

        color_map = {
            1: (185, 185, 185),  # Wall (light gray)
            3: (100, 100, 100),  # Debris (dark gray)
            4: (220, 220, 220),  # Road (light road gray)
            5: (150, 150, 255),  # Building (blue-ish)
        }

        for y in range(self.grid_array.shape[0]):
            for x in range(self.grid_array.shape[1]):
                cell_value = self.grid_array[y, x]
                color = color_map.get(cell_value)
                if color:
                    rect = shapes.Rectangle(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                        color=color,
                        batch=self.batch,
                    )
                    self.shapes.append(rect)

    def draw_player(self):
        # Draw the player (blue)
        player_indices = np.argwhere(self.grid_array == 2)
        player = shapes.Rectangle(
            player_indices[0][1] * self.CELL_SIZE,
            player_indices[0][0] * self.CELL_SIZE,
            self.CELL_SIZE,
            self.CELL_SIZE,
            color=(0, 0, 255),
            batch=self.batch,
        )
        self.player_shapes = [player]  # Store only one player shape

    def move_player(self, dx, dy):
        """Move player on the grid."""
        player_pos = np.argwhere(self.grid_array == 2)[0]
        current_y, current_x = player_pos
        new_y = current_y + dy
        new_x = current_x + dx

        # Check bounds and if new position is free
        if (
            0 <= new_x < self.GRID_WIDTH
            and 0 <= new_y < self.GRID_HEIGHT
            and self.grid_array[new_y, new_x] != 1
            and self.grid_array[new_y, new_x] != 3
        ):
            # Move the player
            self.grid_array[current_y, current_x] = 0  # Set old position to free
            self.grid_array[new_y, new_x] = 2  # Set new position to player
        self.follow_player()

    def update(self, dt):
        self.push_handlers(self.keys)
        if self.keys[pyglet.window.key.UP]:
            self.move_player(0, 1)
        elif self.keys[pyglet.window.key.DOWN]:
            self.move_player(0, -1)
        elif self.keys[pyglet.window.key.LEFT]:
            self.move_player(-1, 0)
        elif self.keys[pyglet.window.key.RIGHT]:
            self.move_player(1, 0)

    def on_draw(self):
        """Draw everything to the window."""
        self.clear()  # Clear the window
        self.draw_player()  # Draw the grid (walls and free space)
        self.batch.draw()  # Draw the player
