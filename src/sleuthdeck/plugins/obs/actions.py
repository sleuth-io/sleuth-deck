import base64
import hashlib
import json
from os import path
from os.path import dirname
from random import randint
from time import sleep
from typing import Any, Callable
from typing import List
from typing import Optional

from obsws_python.error import OBSSDKError
from obsws_python.util import as_dataclass

from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import KeyScene
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window, By

import websocket


# Copied from obsws_python 1.1.1, fixed to support reconnection
class ReconnectingObsClient:
    DELAY = 0.001

    def __init__(self, host: str, port: int, password: str):
        self.ws = websocket.WebSocket()
        self.host = host
        self.port = port
        self.password = password
        self.subs = 0
        self._connected = False

    def connect(self):
        if not self._connected:
            self.ws.connect(f"ws://{self.host}:{self.port}")
            self._authenticate(json.loads(self.ws.recv()))
            self._connected = True

    def _authenticate(self, server_hello):
        secret = base64.b64encode(
            hashlib.sha256(
                (
                    self.password + server_hello["d"]["authentication"]["salt"]
                ).encode()
            ).digest()
        )

        auth = base64.b64encode(
            hashlib.sha256(
                (
                    secret.decode()
                    + server_hello["d"]["authentication"]["challenge"]
                ).encode()
            ).digest()
        ).decode()

        payload = {
            "op": 1,
            "d": {
                "rpcVersion": 1,
                "authentication": auth,
                "eventSubscriptions": self.subs,
            },
        }

        self.ws.send(json.dumps(payload))
        return self.ws.recv()

    def req(self, req_type, req_data=None):
        self.connect()
        if req_data:
            payload = {
                "op": 6,
                "d": {
                    "requestType": req_type,
                    "requestId": randint(1, 1000),
                    "requestData": req_data,
                },
            }
        else:
            payload = {
                "op": 6,
                "d": {"requestType": req_type, "requestId": randint(1, 1000)},
            }
        try:
            self.ws.send(json.dumps(payload))
        except ConnectionError as ex:
            print(f"Disconnected: {ex}")
            self._connected = False
            raise ex
        response = json.loads(self.ws.recv())
        return response["d"]


class OBS:
    def __init__(self, password: str,
                 host: str = "localhost",
                 port: int = 4444, ):
        if not password:
            raise ValueError("Missing password for obs")
        self._started = False
        self.client = ReconnectingObsClient(host=host, port=port, password=password)

    def change_scene(self, name: str):
        return ChangeScene(self, name)

    def close(self):
        return Close(self)

    def toggle_source(self, name: str, show: bool = None, scene: Optional[str] = None):
        return ToggleSource(self, name, show, scene=scene)

    def set_scene_item_enabled(self, scene: str, name: str, enabled: bool = True):
        resp = self.call("GetSceneItemId", {
            "sceneName": scene,
            "sourceName": name,
        })
        self.call("SetSceneItemEnabled", {
            "sceneName": scene,
            "sceneItemId": resp.scene_item_id,
            "sceneItemEnabled": enabled,
        })

    def stop_recording(self):
        return ObsAction(self, lambda obs: obs.call("StopRecord"))

    def start_recording(self):
        return ObsAction(self, lambda obs: obs.call("StartRecord"))

    def set_item_property(self, name: str, property: str, value: Any):
        self.call("SetInputSettings", {"inputName": name,
                                           "inputSettings": {property: value},
                                           "overlay": True})

    def call(self, param, data=None) -> Any:
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
            resp = self.call("GetSceneItemId", {
                "sceneName": scene,
                "sourceName": self.name,
            })
            visible = self.obs.call("GetSceneItemEnabled", {
                "sceneName": self.scene,
                "sceneItemId": resp.scene_item_id,
                }).sceneItemEnabled
        else:
            visible = self._show

        print(f"Making {visible}")

        self.obs.set_scene_item_enabled(self.scene, self.name, visible)
