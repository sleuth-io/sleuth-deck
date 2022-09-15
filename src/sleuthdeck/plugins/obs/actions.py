from os import path
from os.path import dirname
from time import sleep
from typing import Any, Callable
from typing import List
from typing import Optional

from obswebsocket import obsws
from obswebsocket import requests
from obswebsocket.base_classes import Baserequests
from obswebsocket.requests import StopRecording, StartRecording
from websocket import WebSocketConnectionClosedException

from sleuthdeck.actions import SendHotkey
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import KeyScene
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window, By


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

    def close(self):
        return Close(self)

    def toggle_source(self, name: str, show: bool = None, scene: Optional[str] = None):
        return ToggleSource(self, name, show, scene=scene)

    def stop_recording(self):
        return ObsAction(self, lambda obs: obs.obs(StopRecording()))

    def start_recording(self):
        return ObsAction(self, lambda obs: obs.obs(StartRecording()))

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


class Close(Action):
    def __init__(self, obs: OBS):
        self.obs = obs

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        window = get_window(By.window_class("obs.obs"), attempts=1)
        if window:
            self.obs.obs(StopVirtualCam())
            sleep(.5)
            window.close()
            get_window(By.window_class("obs.obs"), attempts=1)
            sleep(.5)


class ChangeScene(Action):
    def __init__(self, obs: OBS, name: str):
        self.name = name
        self.obs = obs

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.obs.obs(requests.SetCurrentScene(self.name))


class ObsAction(Action):
    def __init__(self, obs: OBS, callable: Callable[[OBS], None]):
        self.obs = obs
        self.callable = callable

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.callable(self.obs)


class ToggleSource(Action):
    def __init__(self, obs: OBS, name: str, show: bool = None, scene = None):
        self.name = name
        self.obs = obs
        self.scene = scene
        self._show = show

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        if self._show is None:
            visible = not self.obs.obs(requests.GetSceneItemProperties(self.name)).getVisible()
        else:
            visible = self._show

        print(f"Making {visible}")

        self.obs.obs(requests.SetSceneItemRender(self.name, visible, scene_name=self.scene))


class StopVirtualCam(Baserequests):
    """Stop recording.
Will return an `error` if recording is not active.

    """

    def __init__(self):
        Baserequests.__init__(self)
        self.name = 'StopVirtualCam'
