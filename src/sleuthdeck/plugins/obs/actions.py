from os import path
from os.path import dirname
from typing import Any
from typing import List
from typing import Optional

from obswebsocket import obsws
from obswebsocket import requests
from websocket import WebSocketConnectionClosedException

from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import KeyScene
from sleuthdeck.keys import IconKey


class OBS:
    def __init__(self, password: str,
                 host: str = "localhost",
                 port: int = 4444, ):
        if not password:
            raise ValueError("Missing password for obs")
        self._started = False
        self.ws = obsws(host, port, password)

    def change_scene(self, name: str):
        return ChangeScene(self, name)

    def _ensure_connected(self):
        if self._started:
            return self.ws

        self.ws.connect()
        self._started = True

    def obs(self, *args, **kwargs) -> Any:
        self._ensure_connected()
        try:
            return self.ws.call(*args, **kwargs)
        except WebSocketConnectionClosedException as e:
            self._started = False
            return self.obs(*args, **kwargs)


class OBSKey(IconKey):
    def __init__(
            self,
            text: Optional[str] = None,
            actions: List[Action] = None,
            **kwargs,
    ):
        super().__init__(
            path.join(dirname(__file__), "assets", "obs-logo.png"),
            actions=actions,
            text=text,
            **kwargs,
        )


class ChangeScene(Action):
    def __init__(self, obs: OBS, name: str):
        self.name = name
        self.obs = obs

    def execute(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.obs.obs(requests.SetCurrentScene(self.name))
