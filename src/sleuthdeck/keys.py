from __future__ import annotations

import asyncio
from os import path
from typing import Callable
from typing import List
from typing import Optional

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from sleuthdeck.colors import Color
from sleuthdeck.deck import Action
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.windows import get_windows
from StreamDeck.ImageHelpers import PILHelper


class IconKey(Key):
    def __init__(
        self,
        image_file: Optional[str] = None,
        text: Optional[str] = None,
        actions: List[Action] = None,
        base_path: Optional[str] = None,
    ):
        self._image_file = (
            image_file if not base_path else path.join(base_path, image_file)
        )
        self._text = text
        self.actions = actions
        self._scene = None
        super().__init__(actions=actions)

    def connect(self, scene: KeyScene):
        self._scene = scene
        if self._image_file:
            image = IconKey.load_image(self._scene.deck, self._image_file, self._text)
            self.image = image

    @staticmethod
    def load_image(
        deck, image_file: str, text: Optional[str] = None, background_color: str = None
    ):
        icon = Image.open(image_file)

        bottom_margin = 0 if not text else 20
        image = PILHelper.create_scaled_image(
            deck.stream_deck,
            icon,
            margins=[0, 0, bottom_margin, 0],
            background=background_color,
        )
        if text:
            # Load a custom TrueType font and use it to overlay the key index, draw key
            # label onto the image a few pixels from the bottom of the key.
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype("Roboto-Regular.ttf", 14)
            draw.text(
                (image.width / 2, image.height - 5),
                text=text,
                font=font,
                anchor="ms",
                fill="white",
            )

        return image


async def detect_windows_toggle(
    window_title: str, on_opened: Callable[[], None], on_closed: Callable[[], None]
):
    _window_open = False
    while True:
        windows = get_windows()
        window_open = bool([w for w in windows if w.title == window_title])
        if window_open and not _window_open:
            print("detected open")
            on_opened()
            _window_open = True
        elif not window_open and _window_open:
            print("detected closed")
            on_closed()
            _window_open = False
        await asyncio.sleep(1)
