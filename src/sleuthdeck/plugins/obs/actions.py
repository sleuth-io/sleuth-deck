from os import path
from os.path import dirname
from time import sleep
from typing import Any, Callable
from typing import List
from typing import Optional

from obsws_python.baseclient import ObsClient
from obsws_python.error import OBSSDKError
from obsws_python.util import as_dataclass
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
        self.client = ObsClient(host=host, port=port, password=password)

    def change_scene(self, name: str):
        return ChangeScene(self, name)

    def close(self):
        return Close(self)

    def toggle_source(self, name: str, show: bool = None, scene: Optional[str] = None):
        return ToggleSource(self, name, show, scene=scene)

    def set_scene_item_enabled(self, scene: str, name: str, enabled: bool = True):
        self.call("SetSceneItemEnabled", {
            "sceneName": scene,
            "sceneItemId": name,
            "sceneItemEnabled": enabled,
        })

    def stop_recording(self):
        return ObsAction(self, lambda obs: obs.call("StopRecording"))

    def start_recording(self):
        return ObsAction(self, lambda obs: obs.call("StartRecording"))

    def set_item_property(self, name: str, property: str, value: Any):
        self.call("SetInputSettings", {"inputName": name,
                                           "inputSettings": {property: value},
                                           "overlay": True})

    def _ensure_connected(self):
        if self._started:
            return self.client

        self.client.authenticate()
        self._started = True

    def call(self, param, data=None) -> Any:
        self._ensure_connected()
        response = self.client.req(param, data)
        if not response["requestStatus"]["result"]:
            error = (
                f"Request {response['requestType']} returned code {response['requestStatus']['code']}",
            )
            if "comment" in response["requestStatus"]:
                error += (f"With message: {response['requestStatus']['comment']}",)
            raise OBSSDKError("\n".join(error))
        if "responseData" in response:
            return as_dataclass(response["requestType"], response["responseData"])


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
            self.obs.call("StopVirtualCam")
            sleep(.5)
            window.close()
            get_window(By.window_class("obs.obs"), attempts=1)
            sleep(.5)


class ChangeScene(Action):
    def __init__(self, obs: OBS, name: str):
        self.name = name
        self.obs = obs

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.obs.call("SetCurrentProgramScene", {"sceneName": self.name})


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
            visible = self.obs.call("GetSceneItemEnabled", {
                "sceneName": self.scene,
                "sceneItemId": self.name,
                }).sceneItemEnabled
        else:
            visible = self._show

        print(f"Making {visible}")

        self.obs.set_scene_item_enabled(self.scene, self.name, visible)
