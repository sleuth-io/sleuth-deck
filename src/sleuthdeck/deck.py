from __future__ import annotations

import asyncio
import threading
import time
import traceback
from asyncio import Future
from asyncio import Task
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from enum import auto
from enum import Enum
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from PIL import Image
from sleuthdeck import video
from sleuthdeck.animation import Animations
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck
from StreamDeck.ImageHelpers import PILHelper


class ClickType(Enum):
    CLICK = auto()
    LONG_PRESS = auto()


class Action:
    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        pass


class Updatable:
    async def start(self):
        pass


class Key:
    def __init__(self, image: Optional[Image] = None, actions: List[Action] = None):
        self.image = image
        self.actions = actions if actions is not None else []
        self.clicked_on: Optional[datetime] = None

    def connect(self, scene: KeyScene):
        pass


class Deck:
    def __init__(self):
        print("Scanning for stream decks")
        streamdecks = DeviceManager().enumerate()
        self.stream_deck: StreamDeck = streamdecks[0]
        print(f"Found stream deck: {self.stream_deck.id()}")

        self._animation = Animations(self.stream_deck)
        self._scene = Scene()
        self._last_scene: Scene = self._scene
        self._updating_loop = asyncio.new_event_loop()
        self._updating_thread = threading.Thread(
            target=self._start_background_loop, args=(self._updating_loop,)
        )
        self._updating_thread.start()

    def start_updating(self, task: Awaitable) -> Future:
        return asyncio.run_coroutine_threadsafe(task, loop=self._updating_loop)

    @staticmethod
    def _start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
            tasks = asyncio.all_tasks(loop=loop)
            for t in [t for t in tasks if not (t.done() or t.cancelled())]:
                # give canceled tasks the last chance to run
                loop.run_until_complete(t)
        finally:
            loop.close()

    def __enter__(self):
        if self.stream_deck.is_open():
            self.close()

        self.stream_deck.open()
        self.stream_deck.reset()
        self._animation.start()
        return self

    @property
    def scene(self):
        return self._scene

    def close(self):
        with self.stream_deck:
            self._scene.deactivate()
            self._updating_loop.stop()
            self.stream_deck.reset()
            self.stream_deck.close()

    def new_key_scene(self):
        return KeyScene(self)

    def new_video_scene(self, video_file: str, on_finish: Callable[[], None]):
        return VideoScene(self.stream_deck, video_file, on_finish)

    def change_scene(self, scene: Scene):
        self._scene.deactivate()
        self._last_scene = self._scene
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
        pass

    def previous_scene(self):
        self.change_scene(self._last_scene)


class Scene:
    def activate(self):
        pass

    def deactivate(self):
        pass


class VideoScene:
    def __init__(
        self, stream_deck: StreamDeck, video_file: str, on_finish: Callable[[], None]
    ):
        self._stream_deck = stream_deck
        self._video_file = video_file
        self._on_finish = on_finish

    def activate(self):
        video.show_video(self._stream_deck, self._video_file)
        self._on_finish()

    def deactivate(self):
        pass


@dataclass
class KeyRegistration:
    key: Key
    updator: Optional[Task] = None


class KeyScene(Scene):
    def __init__(self, deck: Deck):
        self._deck = deck
        self._keys: List[KeyRegistration] = [
            KeyRegistration(Key()) for _ in range(deck.stream_deck.KEY_COUNT)
        ]
        self._actions: Dict[Key, List[Action]] = {}
        self._click_thread = None
        self._active = False

    @property
    def deck(self):
        return self._deck

    @property
    def active(self):
        return self._active

    def _check_long_click(self):
        while self._deck.stream_deck.is_open() and self._active:
            for reg in list(self._keys):
                if (
                    reg.key.clicked_on is not None
                    and reg.key.clicked_on
                    < datetime.utcnow() - timedelta(milliseconds=500)
                ):
                    self._run_actions(ClickType.LONG_PRESS, reg.key)
            time.sleep(0.1)

    def _run_actions(self, click: ClickType, key: Key):
        key.clicked_on = None
        actions = list(self._actions.get(key, key.actions))
        for action in actions:
            try:
                print(f"Running {action.__class__.__name__}")
                action.execute(self, key, click)
            except Exception as e:
                print(f"Error running action {action}: {e}")
                traceback.print_exc()

    def add(
        self,
        position: Union[int, Tuple[int, int]],
        key: Key,
        actions: List[Action] = None,
    ):
        if isinstance(position, Tuple):
            position = position[0] * self._deck.stream_deck.KEY_COLS + position[1]
        key.connect(self)
        self._keys[position] = KeyRegistration(key)
        if actions:
            self._actions = actions

    def update_image(self, key: Key):
        if self._active:
            pos = next(pos for pos, reg in enumerate(self._keys) if reg.key == key)
            self._deck.update_key_image(pos, key.image)

    def activate(self):
        self._active = True

        def key_change_callback(_, key_id, state):
            cur_key = self._keys[key_id].key
            if state:
                cur_key.clicked_on = datetime.utcnow()
            elif cur_key.clicked_on:
                self._run_actions(ClickType.CLICK, cur_key)

        for pos, reg in enumerate(self._keys):
            self._deck.update_key_image(pos, reg.key.image)
            if isinstance(reg.key, Updatable):

                future = self._deck.start_updating(
                    self._run_updating_task(reg.key.start())
                )
                reg.updator = future

        self._deck.stream_deck.set_key_callback(key_change_callback)
        self._click_thread = threading.Thread(target=self._check_long_click)
        self._click_thread.start()

    @staticmethod
    async def _run_updating_task(awaitable: Awaitable):
        try:
            await awaitable
        except asyncio.CancelledError:
            # ignore canceled task
            pass
        except Exception as e:
            print(f"Error: {e}")

    def deactivate(self):
        for pos, key in enumerate(self._keys):
            self._deck.update_key_image(pos, None)

        for reg in self._keys:
            if reg.updator:
                reg.updator.cancel()

        self._deck.stream_deck.set_key_callback(None)
        self._active = False
        self._click_thread = None
