from __future__ import annotations
import threading
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import List, Callable, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck
from StreamDeck.ImageHelpers import PILHelper

from sleuthdeck import video
from sleuthdeck.animation import Animations


class ClickType(Enum):
    CLICK = auto()
    LONG_PRESS = auto()


class Key:
    def __init__(self, image: Optional[Image] = None, on_click: Callable[[ClickType], None] = None):
        self.image = image
        self.on_click = on_click if on_click is not None else lambda *_: None
        self.clicked_on: Optional[datetime] = None

    def connect(self, deck: Deck):
        pass


class IconKey(Key):
    def __init__(self, image_file: Optional[str] = None, text: Optional[str] = None,
                 on_click: Callable[[ClickType], None] = None):
        self._image_file = image_file
        self._text = text
        super().__init__(on_click=on_click)

    def connect(self, deck: Deck):
        if self._image_file:
            image = IconKey.load_image(deck, self._image_file, self._text)
            self.image = image

    @staticmethod
    def load_image(deck, image_file: str, text: Optional[str] = None):
        icon = Image.open(image_file)
        bottom_margin = 0 if not text else 20
        image = PILHelper.create_scaled_image(deck.stream_deck, icon, margins=[0, 0, bottom_margin, 0])
        if text:
            # Load a custom TrueType font and use it to overlay the key index, draw key
            # label onto the image a few pixels from the bottom of the key.
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype("Roboto-Regular.ttf", 14)
            draw.text((image.width / 2, image.height - 5), text=text, font=font, anchor="ms", fill="white")
        return image


class Deck:
    def __init__(self):
        streamdecks = DeviceManager().enumerate()
        self.stream_deck: StreamDeck = streamdecks[0]
        self._animation = Animations(self.stream_deck)
        self._scene = Scene()

    def __enter__(self):
        self.stream_deck.open()
        self.stream_deck.reset()
        self._animation.start()
        return self

    @property
    def scene(self):
        return self._scene

    def close(self):
        with self.stream_deck:
            self.stream_deck.reset()
            self.stream_deck.close()

    def new_key_scene(self):
        return KeyScene(self)

    def new_video_scene(self, video_file: str, on_finish: Callable[[], None]):
        return VideoScene(self.stream_deck, video_file, on_finish)

    def change_scene(self, scene: Scene):
        self._scene.deactivate()
        self._scene = scene
        self._scene.activate()

    def update_key_image(self, pos: int, image: Optional[Image]):
        if image:
            if getattr(image, "is_animated", False):
                self._animation.add(pos, image)
            else:
                native_image = PILHelper.to_native_format(self.stream_deck, image)
                self.stream_deck.set_key_image(pos, native_image)
                self._animation.clear(pos)
        else:
            self.stream_deck.set_key_image(pos, None)
            self._animation.clear(pos)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass


class Scene:
    def activate(self):
        pass

    def deactivate(self):
        pass


class VideoScene:
    def __init__(self, stream_deck: StreamDeck, video_file: str, on_finish: Callable[[], None]):
        self._stream_deck = stream_deck
        self._video_file = video_file
        self._on_finish = on_finish

    def activate(self):
        video.show_video(self._stream_deck, self._video_file)
        self._on_finish()

    def deactivate(self):
        pass


class KeyScene(Scene):
    def __init__(self, deck: Deck):
        self._deck = deck
        self._keys: List[Key] = [Key() for _ in range(
            deck.stream_deck.KEY_COUNT)]
        self._click_thread = None
        self._active = False

    def _check_long_click(self):
        while self._deck.stream_deck.is_open() and self._active:
            for key in list(self._keys):
                if key.clicked_on is not None and key.clicked_on < datetime.utcnow() - timedelta(milliseconds=500):
                    key.clicked_on = None
                    key.on_click(ClickType.LONG_PRESS)
            time.sleep(.1)

    def add(self, position: Union[int, Tuple[int, int]], key: Key):
        if isinstance(position, Tuple):
            position = position[0] * self._deck.stream_deck.KEY_COLS + position[1]
        key.connect(self._deck)
        self._keys[position] = key

    def activate(self):
        self._active = True

        def key_change_callback(_, key_id, state):
            cur_key = self._keys[key_id]
            if state:
                cur_key.clicked_on = datetime.utcnow()
            elif cur_key.clicked_on:
                cur_key.clicked_on = None
                cur_key.on_click(ClickType.CLICK)

        for pos, key in enumerate(self._keys):
            self._deck.update_key_image(pos, key.image)

        self._deck.stream_deck.set_key_callback(key_change_callback)
        self._click_thread = threading.Thread(target=self._check_long_click)
        self._click_thread.start()

    def deactivate(self):
        for pos, key in enumerate(self._keys):
            self._deck.update_key_image(pos, None)

        self._deck.stream_deck.set_key_callback(None)
        self._active = False
        self._click_thread = None
