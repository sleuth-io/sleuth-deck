from __future__ import annotations
import signal
import subprocess
from time import sleep
from typing import Optional, Union, Tuple

from PIL.Image import Image
from pyautogui import hotkey

from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Scene
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window, By


class Command(Action):
    def __init__(self, command: str, *args: str):
        self.command = command
        self.args = args

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        print(f"Running {self.command} {' '.join(self.args)}")
        subprocess.run([self.command] + list(self.args))


class Toggle(Action):
    def __init__(self, on_enable: Command, on_disable: Command, initial: bool = False) -> None:
        self._on_enable = on_enable
        self._on_disable = on_disable
        self._state = initial

    def execute(self, scene: KeyScene, key: IconKey, click: ClickType):
        if self._state:
            self._on_disable.execute(scene, key, click)
            key.update_icon(enabled=False)
            self._state = False
        else:
            self._on_enable.execute(scene, key, click)
            key.update_icon(enabled=True)
            self._state = True


class ChangeScene(Action):
    def __init__(self, scene: Scene):
        self.scene = scene

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        scene.deck.change_scene(self.scene)


class PreviousScene(Action):
    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        scene.deck.previous_scene()


class Close(Action):
    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        scene.deck.close()
        signal.raise_signal(signal.SIGINT)


class MaximizeWindow(Action):
    def __init__(self, title: Union[str, By]):
        self.title = title

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=5 * 10)
        if window:
            window.maximize()
        else:
            print("No window found")


class UnMaximizeWindow(Action):
    def __init__(self, title: Union[str, By]):
        self.title = title

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=5 * 10)
        if window:
            window.unmaximize()
        else:
            print("No window found")


class Pause(Action):
    def __init__(self, seconds: Union[float, int]):
        self.seconds = seconds

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        sleep(self.seconds)


class CloseWindow(Action):
    def __init__(self, title: Union[str, By], wait=5):
        self.title = title
        self._wait = wait

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=self._wait * 10)
        if window:
            window.close()
        else:
            print(f"No window found with {self.title}")


class MoveWindow(Action):
    def __init__(self, title: Union[str, By], x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window(self.title, attempts=5 * 10)
        if window:
            window.move(self.x, self.y, self.width, self.height)
        else:
            print("No window found")


class SendHotkey(Action):
    def __init__(self, title: Union[str, By], *hotkey: str):
        self.title = title
        self.hotkey = hotkey

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        print("sending key")
        window = get_window(self.title, attempts=5 * 10)
        print("got window")
        window.focus()
        hotkey(*self.hotkey)
        print("sent")


class ToggleSleep(Action):
    def __init__(self) -> None:
        self._sleep = False

    def execute(self, scene: KeyScene, key: IconKey, click: ClickType):
        if self._sleep:
            scene.deck.stream_deck.set_brightness(5)
            self._sleep = False
        else:
            scene.deck.stream_deck.set_brightness(70)
            self._sleep = True
