from os import path
from os.path import dirname
from typing import List
from typing import Optional
from urllib.parse import urlparse

from sleuthdeck.actions import CloseWindow
from sleuthdeck.actions import Command
from sleuthdeck.actions import MaximizeWindow
from sleuthdeck.deck import Action
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Updatable
from sleuthdeck.keys import detect_windows_toggle
from sleuthdeck.keys import IconKey


class StartMeetingKey(IconKey, Updatable):
    def __init__(
        self,
        url: str = None,
        text: Optional[str] = None,
        actions: List[Action] = None,
        **kwargs,
    ):
        self._original_actions = list(actions if actions else [StartMeeting(url)])
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
        self.image = IconKey.load_image(
            self._scene.deck,
            self._image_file,
            f"{self._text} (Call)",
            background_color="red",
        )
        self._scene.update_image(self)
        self.actions.clear()
        self.actions.append(EndMeeting())

    def _on_closed(self):
        self.image = IconKey.load_image(
            self._scene.deck, self._image_file, f"{self._text}"
        )
        self._scene.update_image(self)
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


class EndMeeting(CloseWindow):
    def __init__(self):
        super().__init__("Zoom Meeting")
