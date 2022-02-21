from os import path
from os import path
from os.path import dirname
from time import sleep
from typing import List
from typing import Optional
from urllib.parse import urlparse

from pyautogui import press

from sleuthdeck.actions import Command
from sleuthdeck.actions import SendHotkey
from sleuthdeck.deck import Action, Key, ClickType
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Updatable
from sleuthdeck.keys import IconKey
from sleuthdeck.keys import detect_windows_toggle
from sleuthdeck.windows import get_window


class StartMeetingKey(IconKey, Updatable):
    def __init__(
        self,
        url: str = None,
        text: Optional[str] = None,
        actions: List[Action] = None,
        close_actions: List[Action] = None,
        **kwargs,
    ):
        self._original_actions = list(actions if actions else [StartMeeting(url)])
        self._close_actions = close_actions if close_actions else [EndMeeting()]
        super().__init__(
            image_file=path.join(dirname(__file__), "assets", "us.zoom.Zoom.png"),
            actions=list(self._original_actions),
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
        self.update_icon(enabled=True)
        self.actions.clear()
        self.actions.extend(self._close_actions)

    def _on_closed(self):
        self.update_icon(enabled=False)
        self.actions.clear()
        self.actions.extend(self._original_actions)


class StartMeeting(Command):
    def __init__(self, url: str):
        result = urlparse(url)
        meeting_id = result.path.split("/")[-1]
        super().__init__(
            "xdg-open",
            f"zoommtg://{result.hostname}/join?action=join&confno={meeting_id}",
        )


class EndMeeting(SendHotkey):
    def __init__(self):
        super().__init__("Zoom Meeting", "alt", "q")

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        super().execute(scene, key, click)
        w = get_window("Zoom Meeting")
        if w:
            w.focus()
            sleep(.5)
            print("pressing enter")
            press("enter")



