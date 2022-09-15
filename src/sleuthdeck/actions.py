from __future__ import annotations

import os
import signal
import subprocess
from time import sleep
from typing import Optional, Union, Tuple

from PIL.Image import Image

from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Scene
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window, By, get_windows, get_focused_window


class Sequential(Action):
    def __init__(self, *actions: Action) -> None:
        super().__init__()
        self._actions = actions

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        for action in self._actions:
            action(scene, key, click)


class Command(Action):
    def __init__(self, command: str, *args: str):
        self.command = command
        self.args = args

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        print(f"Running {self.command} {' '.join(self.args)}")
        subprocess.run([self.command] + list(self.args))


class Wait(Action):
    def __init__(self, seconds: int = 1):
        self.seconds = seconds

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        sleep(self.seconds)


class Toggle(Action):
    def __init__(self, on_enable: Union[list[Action], Action], on_disable: Union[list[Action], Action], initial: bool = False) -> None:
        self._on_enable = on_enable if not isinstance(on_enable, list) else Sequential(*on_enable)
        self._on_disable = on_disable if not isinstance(on_disable, list) else Sequential(*on_disable)
        self._state = initial

    def __call__(self, scene: KeyScene, key: IconKey, click: ClickType):
        if self._state:
            self._on_disable(scene, key, click)
            key.update_icon(enabled=False)
            self._state = False
        else:
            self._on_enable(scene, key, click)
            key.update_icon(enabled=True)
            self._state = True


class ChangeScene(Action):
    def __init__(self, scene: Scene):
        self.scene = scene

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        scene.deck.change_scene(self.scene)


class PreviousScene(Action):
    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        scene.deck.previous_scene()


class Close(Action):
    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        scene.deck.close()
        signal.raise_signal(signal.SIGINT)


class MaximizeWindow(Action):
    def __init__(self, title: Union[str, By]):
        self.title = title

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=5 * 10)
        if window:
            window.maximize()
        else:
            print("No window found")


class UnMaximizeWindow(Action):
    def __init__(self, title: Union[str, By]):
        self.title = title

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=5 * 10)
        if window:
            window.unmaximize()
        else:
            print("No window found")


class Pause(Action):
    def __init__(self, seconds: Union[float, int]):
        self.seconds = seconds

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        sleep(self.seconds)


class CloseWindow(Action):
    def __init__(self, title: Union[str, By], wait=5):
        self.title = title
        self._wait = wait

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=self._wait * 10)
        if window:
            print(f"Closing window {self.title}")
            window.close()
            print(f"Closed window {self.title}")
        else:
            print(f"No window found with {self.title}")


class MoveWindow(Action):
    def __init__(self, title: Union[str, By], x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=5 * 10)
        if window:
            window.move(self.x, self.y, self.width, self.height)
        else:
            print("No window found")


class SendHotkey(Action):
    def __init__(self, title: Union[str, By], *hotkey: str):
        self.title = title
        self.hotkey = hotkey

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        print("sending key")
        focused_window = get_focused_window()

        window = get_window(self.title, attempts=5 * 10)
        if not window:
            print(f"No window found for {self.title}")
            return
        print(f"got window {self.title}")
        window.focus()
        from pyautogui import hotkey
        hotkey(*self.hotkey)
        print("sent")
        focused_window.focus()


class DeckBrightness(Action):
    def __init__(self, value: int) -> None:
        self._value = value

    def __call__(self, scene: KeyScene, key: IconKey, click: ClickType):
        scene.deck.stream_deck.set_brightness(self._value)
