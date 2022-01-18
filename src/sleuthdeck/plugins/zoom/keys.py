import asyncio
import subprocess
from os import path
from os.path import dirname
from typing import Optional
from urllib.parse import urlparse

from sleuthdeck import shell
from sleuthdeck.actions import Command
from sleuthdeck.colors import Color
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Updatable
from sleuthdeck.keys import detect_windows_toggle
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window


class StartMeetingKey(IconKey, Updatable):
    def __init__(self, url: str = None, text: Optional[str] = None, **kwargs):
        super().__init__(
            image_file=path.join(dirname(__file__), "assets", "us.zoom.Zoom.png"),
            actions=[StartMeetingAction(url)],
            text=text,
            **kwargs,
        )
        super()
        self._scene: Optional[KeyScene] = None
        self._url = url

    def connect(self, scene: KeyScene):
        self._scene = scene
        super().connect(scene)

    async def start(self):
        await detect_windows_toggle(
            "Zoom Meeting", on_opened=self._on_opened, on_closed=self._on_closed
        )

    def _on_opened(self):
        self.image = IconKey.load_image(
            self._scene.deck,
            self._image_file,
            f"{self._text} (Call)",
            background_color="red",
        )
        self._scene.update_image(self)
        self.actions.clear()
        self.actions.append(EndMeetingAction())

    def _on_closed(self):
        self.image = IconKey.load_image(
            self._scene.deck, self._image_file, f"{self._text}"
        )
        self._scene.update_image(self)
        self.actions.clear()
        self.actions.append(StartMeetingAction(self._url))


class StartMeetingAction(Command):
    def __init__(self, url: str):
        result = urlparse(url)
        meeting_id = result.path.split("/")[-1]
        super().__init__(
            "xdg-open",
            f"zoommtg://{result.hostname}/join?action=join&confno={meeting_id}",
        )


class EndMeetingAction(Action):
    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window("Zoom Meeting")
        if window:
            window.close()
        else:
            print("No meeting to end")
