import arcade


class TransitionView(arcade.View):
    def __init__(self, previous_view, next_factory, style="fade"):
        super().__init__()
        self.previous = previous_view
        self.next_factory = next_factory
        self.next_view = None
        self.style = style
        self.elapsed = 0.0
        self.duration = 1.0

    def on_update(self, dt):
        self.elapsed += dt

        if self.elapsed >= self.duration / 2 and self.next_view is None:
            self.next_view = self.next_factory()

            # Replace the scenes' old fade/slide with this transition.
            if hasattr(self.next_view, "fade_alpha"):
                self.next_view.fade_alpha = 0

            if hasattr(self.next_view, "slide_offset"):
                self.next_view.slide_offset = 0

            # Let the scene leave its INTRO state.
            self.next_view.on_update(0)

        if self.elapsed >= self.duration:
            self.window.show_view(self.next_view)

    def _rect(self, x, y, width, height, colour):
        if width > 0 and height > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(x, y, width, height), colour
            )

    def on_draw(self):
        view = self.next_view or self.previous
        view.on_draw()

        w, h = self.window.width, self.window.height
        progress = min(1.0, self.elapsed / self.duration)

        # Smoothly cover the old scene, then uncover the next.
        amount = (
            progress * 2
            if progress < 0.5
            else (1 - progress) * 2
        )
        amount = amount * amount * (3 - 2 * amount)
        colour = (8, 25, 27)

        if self.style == "door":
            # The opening closes towards the restaurant doorway.
            cx, cy = w * 0.78, h * 0.30
            left = cx * amount
            right = w - (w - cx) * amount
            bottom = cy * amount
            top = h - (h - cy) * amount

            self._rect(left / 2, h / 2, left, h, colour)
            self._rect(
                (right + w) / 2, h / 2,
                w - right, h, colour
            )
            self._rect(
                (left + right) / 2, bottom / 2,
                right - left, bottom, colour
            )
            self._rect(
                (left + right) / 2, (top + h) / 2,
                right - left, h - top, colour
            )

        elif self.style == "curtain":
            width = w * amount / 2
            self._rect(width / 2, h / 2, width, h, colour)
            self._rect(w - width / 2, h / 2, width, h, colour)

        elif self.style == "bands":
            # Alternating pixel-style strips.
            rows = 12
            height = h / rows
            width = w * amount

            for row in range(rows):
                x = width / 2 if row % 2 == 0 else w - width / 2
                self._rect(
                    x, (row + 0.5) * height,
                    width, height + 1, colour
                )

        else:
            self._rect(
                w / 2, h / 2, w, h,
                (8, 25, 27, int(255 * amount))
            )
