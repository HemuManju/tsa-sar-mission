import random

import numpy as np


class GridWorldGenerator:
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid_array = np.zeros((grid_height, grid_width), dtype=int)

    def _add_outer_boundary(self):
        """Add a wall around the edges of the grid."""
        self.grid_array[0, :] = 1  # Top row
        self.grid_array[-1, :] = 1  # Bottom row
        self.grid_array[:, 0] = 1  # Left column
        self.grid_array[:, -1] = 1  # Right column

    def generate_walls(self):
        """Generate different types of walls in the grid."""

        # Add outer boundary
        self._add_outer_boundary()

        wall_types = [
            "U",
            "T",
            "L",
            "I",
        ]  # 'U' for U-shape, 'T' for T-shape, 'L' for L-shape, 'I' for straight walls
        for _ in range(random.randint(20, 30)):  # Random number of walls to place
            wall_type = random.choice(wall_types)
            y = random.randint(1, self.grid_height - 4)  # Random row for wall placement
            x = random.randint(
                1, self.grid_width - 4
            )  # Random column for wall placement

            if wall_type == "U":
                self.place_u_wall(x, y)
            elif wall_type == "T":
                self.place_t_wall(x, y)
            elif wall_type == "L":
                self.place_l_wall(x, y)
            elif wall_type == "I":
                self.place_straight_wall(x, y)

    def place_u_wall(self, x, y):
        """Place a U-shaped wall at position (x, y)."""
        self.grid_array[y, x : x + 3] = 1  # Top of the U
        self.grid_array[y + 1, x] = 1  # Left side of the U
        self.grid_array[y + 1, x + 2] = 1  # Right side of the U
        self.grid_array[y + 2, x] = 1  # Bottom left corner
        self.grid_array[y + 2, x + 2] = 1  # Bottom right corner

    def place_t_wall(self, x, y):
        """Place a T-shaped wall at position (x, y)."""
        self.grid_array[y, x : x + 3] = 1  # Horizontal line of the T
        self.grid_array[y + 1, x + 1] = 1  # Vertical line of the T

    def place_l_wall(self, x, y):
        """Place an L-shaped wall at position (x, y)."""
        self.grid_array[y, x : x + 3] = 1  # Top horizontal line of the L
        self.grid_array[y + 1, x] = 1  # Vertical line of the L

    def place_straight_wall(self, x, y):
        """Place a straight vertical or horizontal wall at position (x, y)."""
        if random.choice(
            [True, False]
        ):  # Randomly choose if it's horizontal or vertical
            self.grid_array[y, x : x + 3] = 1  # Horizontal wall
        else:
            self.grid_array[y : y + 3, x] = 1  # Vertical wall

    def get_grid(self):
        """Return the generated grid with walls."""
        return self.grid_array
