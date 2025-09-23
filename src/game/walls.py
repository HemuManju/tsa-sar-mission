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
        self._add_outer_boundary()

        wall_types = ["U", "T", "L", "I"]
        for _ in range(random.randint(20, 30)):
            wall_type = random.choice(wall_types)
            y = random.randint(1, self.grid_height - 4)
            x = random.randint(1, self.grid_width - 4)

            if wall_type == "U":
                self.place_u_wall(x, y)
            elif wall_type == "T":
                self.place_t_wall(x, y)
            elif wall_type == "L":
                self.place_l_wall(x, y)
            elif wall_type == "I":
                self.place_straight_wall(x, y)

        self._decay_walls()
        self._scatter_debris()

    def place_u_wall(self, x, y):
        self.grid_array[y, x : x + 3] = 1
        self.grid_array[y + 1, x] = 1
        self.grid_array[y + 1, x + 2] = 1
        self.grid_array[y + 2, x] = 1
        self.grid_array[y + 2, x + 2] = 1

    def place_t_wall(self, x, y):
        self.grid_array[y, x : x + 3] = 1
        self.grid_array[y + 1, x + 1] = 1

    def place_l_wall(self, x, y):
        self.grid_array[y, x : x + 3] = 1
        self.grid_array[y + 1, x] = 1

    def place_straight_wall(self, x, y):
        if random.choice([True, False]):
            self.grid_array[y, x : x + 3] = 1
        else:
            self.grid_array[y : y + 3, x] = 1

    def _decay_walls(self, decay_chance=0.3):
        """Randomly remove wall blocks to simulate damage."""
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                if self.grid_array[y, x] == 1 and random.random() < decay_chance:
                    self.grid_array[y, x] = 0

    def _scatter_debris(self, num_debris=50):
        """Randomly place debris blocks (value 3) around the grid."""
        for _ in range(num_debris):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(1, self.grid_height - 2)
            if self.grid_array[y, x] == 0:
                self.grid_array[y, x] = 3  # 3 = debris

    def get_grid(self):
        return self.grid_array
