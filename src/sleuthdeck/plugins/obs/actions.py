from os import path
from os.path import dirname
from time import sleep
from typing import Any
from typing import Callable
from typing import List
from typing import Optional

from obswebsocket import obsws
from obswebsocket import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from sleuthdeck.colors import Color
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Updatable
from sleuthdeck.keys import detect_windows_toggle
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window
from websocket import WebSocketConnectionClosedException


class OBSKey(IconKey):
    def __init__(
        self,
        password: str,
        host: str = "localhost",
        port: int = 4444,
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
        self._driver: Optional[WebDriver] = None
        self._started = False
        self.ws = obsws(host, port, password)

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


class ChangeScene(Action):
    def __init__(self, name: str):
        self.name = name

    def execute(self, scene: KeyScene, key: OBSKey, click: ClickType):
        key.obs(requests.SetCurrentScene(self.name))
