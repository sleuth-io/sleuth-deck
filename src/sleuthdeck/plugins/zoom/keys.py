import asyncio
import subprocess
from os import path
from os.path import dirname
from typing import Optional
from urllib.parse import urlparse

from sleuthdeck.actions import Command
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import IconKey
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Updatable


class StartMeetingKey(IconKey, Updatable):
    def __init__(self, url: str = None, text: Optional[str] = None):
        super().__init__(
            image_file=path.join(dirname(__file__), "assets", "us.zoom.Zoom.png"),
            actions=[StartMeetingAction(url)],
            text=text,
        )
        self._scene: Optional[KeyScene] = None
        self._url = url
        self._in_call = False

    def connect(self, scene: KeyScene):
        self._scene = scene
        super().connect(scene)

    async def start(self):
        while True:
            result = subprocess.run(
                ["wmctrl", "-lx"], stdout=subprocess.PIPE, text=True
            )
            meeting_window_open = "Zoom Meeting" in result.stdout
            if meeting_window_open and not self._in_call:
                print("detected call")
                self.image = IconKey.load_image(
                    self._scene.deck, self._image_file, f"{self._text} (Call)"
                )
                self._scene.update_image(self)
                self._in_call = True
                self.actions.clear()
                self.actions.append(EndMeetingAction())
            elif not meeting_window_open and self._in_call:
                print("detected no call)")
                self.image = IconKey.load_image(
                    self._scene.deck, self._image_file, f"{self._text}"
                )
                self._in_call = False
                self._scene.update_image(self)
                self.actions.clear()
                self.actions.append(StartMeetingAction(self._url))
            await asyncio.sleep(1)


class StartMeetingAction(Command):
    def __init__(self, url: str):
        result = urlparse(url)
        meeting_id = result.path.split("/")[-1]
        super().__init__(
            "xdg-open",
            f"zoommtg://{result.hostname}/join?action=join&confno={meeting_id}",
        )


class EndMeetingAction(Action):
    def execute(self, scene: KeyScene, click: ClickType):
        result = subprocess.run(["wmctrl", "-lx"], stdout=subprocess.PIPE, text=True)
        for line in result.stdout.split("\n"):
            if "Zoom Meeting" in line:
                window_id = line.split(" ")[0]
                subprocess.run(["wmctrl", "-ic", window_id])
                break
        else:
            print("No meeting to end")
