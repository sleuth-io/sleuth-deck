from __future__ import annotations

import asyncio
from functools import partial
from io import BytesIO
from os import path
from os.path import dirname
from typing import Callable
from typing import List
from typing import Optional

from PIL import Image, ImageEnhance, ImageOps, ImageColor
from PIL import ImageDraw
from PIL import ImageFont
from PIL.ImageColor import getrgb, getcolor
from PIL.ImageOps import grayscale
from cairosvg import svg2png

from sleuthdeck.colors import Color
from sleuthdeck.deck import Action
from sleuthdeck.deck import Key, Deck
from sleuthdeck.deck import KeyScene
from sleuthdeck.windows import get_windows
from StreamDeck.ImageHelpers import PILHelper


ENABLED_MARGIN = 5
ENABLED_COLOR = "red"


class IconKey(Key):
    def __init__(
        self,
        image_file: Optional[str] = None,
        text: Optional[str] = None,
        actions: List[Action] = None,
        base_path: Optional[str] = None,
        image_loader: Callable[[Deck], Image] = None
    ):

        full_path = (
            image_file if not base_path else path.join(base_path, image_file)
        )
        self.actions = actions
        self._scene = None
        if not image_loader:
            image_loader = partial(IconKey.load_image, image_file=full_path, text=text)

        self._image_loader = image_loader
        super().__init__(actions=actions)

    def update_icon(self, **kwargs):
        self._image_loader = partial(self._image_loader, **kwargs)
        self.image = self._image_loader()
        self._scene.update_image(self)

    def connect(self, scene: KeyScene):
        self._scene = scene
        self._image_loader = partial(self._image_loader, deck=scene.deck)
        image = self._image_loader()
        self.image = image

    @staticmethod
    def load_image(
        deck, image_file: str, text: Optional[str] = None, background_color: str = "black", tint: str = None,
            enabled: bool = False, inverse: bool = False
    ):
        text_margin = 0 if not text else 14
        margin = [text_margin, 0, 0, 0]
        if enabled:
            margin = [x+ENABLED_MARGIN for x in margin]

        if image_file.endswith(".svg"):
            with open(image_file, "rb") as f:
                key_x, key_y = deck.stream_deck.key_image_format()["size"]
                key_y -= text_margin
                png = svg2png(file_obj=f, output_width=key_x, output_height=key_y)
                icon = Image.open(BytesIO(png))
                if tint:
                    icon = image_tint(icon, tint=tint)
        else:
            icon = Image.open(image_file)

        if inverse:
            icon = image_inverse(icon)
            bg = getrgb(background_color)
            background_color = (
                255 - bg[0],
                255 - bg[1],
                255 - bg[2]
            )

        image = PILHelper.create_scaled_image(
            deck.stream_deck,
            icon,
            margins=margin,
            background=background_color,
        )
        if text:
            # Load a custom TrueType font and use it to overlay the key index, draw key
            # label onto the image a few pixels from the bottom of the key.
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(path.join(dirname(__file__), "assets", "Roboto-Regular.ttf"), 14)
            draw.text(
                (image.width / 2, margin[0] - 2),
                text=text,
                font=font,
                anchor="ms",
                fill="white",
            )

        if enabled:
            image = ImageOps.expand(image, border=ENABLED_MARGIN, fill=getrgb(ENABLED_COLOR))

        return image


class FontAwesomeKey(IconKey):

    def __init__(self, name: str, text: Optional[str] = None, actions: List[Action] = None, tint: str = "white"):
        super().__init__(path.join(dirname(__file__), "../assets/fontawesome-free-6.0.0-desktop/svgs",
                                   f"{name}.svg"), text, actions)
        self._image_loader = partial(self._image_loader, tint=tint)


async def detect_windows_toggle(
    window_title: str, on_opened: Callable[[], None], on_closed: Callable[[], None]
):
    _window_open = False
    while True:
        windows = get_windows()
        window_open = bool([w for w in windows if w.title == window_title])
        if window_open and not _window_open:
            print(f"Detected window '{window_title}' open")
            on_opened()
            _window_open = True
        elif not window_open and _window_open:
            print(f"Detected window '{window_title}' closed")
            on_closed()
            _window_open = False
        await asyncio.sleep(1)


def image_tint(src, tint='#ffffff'):
    d = src.getdata()

    tint = ImageColor.getrgb(tint)
    new_image = []
    for item in d:
        new_image.append(tint + (item[3],))

    # update image data
    src.putdata(new_image)
    return src


def image_inverse(src):
    d = src.getdata()

    new_image = []
    for item in d:
        new_image.append((
            255-item[0],
            255-item[1],
            255-item[2],
            item[3]
        ))

    # update image data
    src.putdata(new_image)
    return src