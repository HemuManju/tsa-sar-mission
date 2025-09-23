from pyglet.math import Mat4, Vec3


class Camera:
    def __init__(self, screen_width, screen_height, zoom=1.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cam_x = 0
        self.cam_y = 0
        self.zoom = zoom
        self.min_zoom = 0.5
        self.max_zoom = 4.0
        self.viewport_margin = 20  # Pixels before the camera pans

    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates."""
        return (
            (x - self.cam_x) * self.zoom + self.screen_width / 2,
            (y - self.cam_y) * self.zoom + self.screen_height / 2,
        )

    def screen_to_world(self, x, y):
        """Convert screen coordinates to world coordinates."""
        return (
            (x - self.screen_width / 2) / self.zoom + self.cam_x,
            (y - self.screen_height / 2) / self.zoom + self.cam_y,
        )

    def apply_zoom(self, scroll_y, zoom_speed=0.1):
        self.zoom += scroll_y * zoom_speed
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))

    def center_player(self, target_x, target_y):
        self.cam_x, self.cam_y = target_x, target_y

    def keep_target_in_view(self, target_x, target_y):
        """Pan the camera to keep a target (e.g., player) in view."""

        half_w = self.screen_width / (2 * self.zoom)
        half_h = self.screen_height / (2 * self.zoom)

        left = self.cam_x - half_w + self.viewport_margin
        right = self.cam_x + half_w - self.viewport_margin
        bottom = self.cam_y - half_h + self.viewport_margin
        top = self.cam_y + half_h - self.viewport_margin

        if target_x < left:
            self.cam_x = target_x - self.viewport_margin + half_w
        elif target_x > right:
            self.cam_x = target_x + self.viewport_margin - half_w

        if target_y < bottom:
            self.cam_y = target_y - self.viewport_margin + half_h
        elif target_y > top:
            self.cam_y = target_y + self.viewport_margin - half_h

    def get_view_matrix(self):
        """Return the transformation matrix to apply in on_draw."""

        translate_to_origin = Mat4.from_translation(Vec3(-self.cam_x, -self.cam_y, 0))
        scale_matrix = Mat4.from_scale(Vec3(self.zoom, self.zoom, 1.0))
        translate_to_center = Mat4.from_translation(
            Vec3(self.screen_width / 2, self.screen_height / 2, 0)
        )

        return translate_to_center @ scale_matrix @ translate_to_origin
