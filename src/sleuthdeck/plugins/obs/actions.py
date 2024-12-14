import base64
import hashlib
import json
from collections import namedtuple
from dataclasses import dataclass
from os import path
from os.path import dirname
from random import randint
from time import sleep
from typing import Any, Callable
from typing import List
from typing import Optional

import pyautogui
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

    def stop_recording(self, vertical=False):
        def execute(obs):
            obs.call("StopRecord")
            if vertical:
                obs.call("CallVendorRequest", {"vendorName": "aitum-vertical-canvas", "requestType": "stop_recording"})

        return ObsAction(self, execute)


    def start_recording(self, vertical=False):
        def execute(obs):
            obs.call("StartRecord")
            if vertical:
                obs.call("CallVendorRequest", {"vendorName": "aitum-vertical-canvas", "requestType": "start_recording"})
        return ObsAction(self, execute)

    def set_item_property(self, name: str, property: str, value: Any):
        self.call("SetInputSettings", {"inputName": name,
                                       "inputSettings": {property: value},
                                       "overlay": True})

    def create_record_chapter(self, name: str):
        self.call("CreateRecordChapter", {"chapterName": name})

    def get_filter_settings(self, source_name: str, filter_name: str):
        return self.call("GetSourceFilter", {"sourceName": source_name,
                                             "filterName": filter_name})

    def set_filter_properties(self, source_name: str, filter_name: str, **kwargs):
        print(f"setting properties {kwargs}")
        self.call("SetSourceFilterSettings", {"sourceName": source_name,
                                              "filterName": filter_name,
                                              "filterSettings": kwargs})

    def toggle_filter(self, source_name: str, filter_name: str, enabled: bool = True):
        self.call("SetSourceFilterEnabled", {"sourceName": source_name,
                                              "filterName": filter_name,
                                              "filterEnabled": enabled})

    def call_vendor(self, vendor: str, param: str, data=None) -> Any:
        return self.call("CallVendorRequest", dict(
            requestType=param,
            requestData=data,
            vendorName=vendor,
        ))

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
            sleep(5)


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
    def __init__(self, obs: OBS, name: str, show: bool = None, scene=None):
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


@dataclass
class Crop:
    top: int
    bottom: int
    left: int
    right: int


class ZoomToMouse(Action):
    def __init__(self, obs: OBS, scene: str, move_filter_name: str, source_crop: Crop):
        self.obs = obs
        self.scene = scene
        self.move_filter_name = move_filter_name
        self.crop = source_crop

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        import gi
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk

        gdkdsp = Gdk.Display.get_default()

        screen, x, y, _ = gdkdsp.get_pointer()
        monitor = gdkdsp.get_monitor_at_point(x, y)
        geo = monitor.get_geometry()
        # print(f"pointer: x:{x - geo.x} y:{y - geo.y}")

        viewport_width = 1920
        viewport_height = 1080
        zoom_factor = 1.0

        mouse_pos = namedtuple("Point", "x y")(x - geo.x, y - geo.y)

        # settings = self.obs.get_filter_settings(self.scene, self.move_filter_name)
        # print(f"settings: {settings}, crop: {settings.filter_settings['crop']}")

        new_y = max(min(0, ((mouse_pos.y - self.crop.top) * zoom_factor - (viewport_height / 2)) * -1), (geo.height - viewport_height - (self.crop.bottom + self.crop.top)) * -1)
        new_x = max(min(0, ((mouse_pos.x - self.crop.left) * zoom_factor - (viewport_width / 2)) * -1), (geo.width - viewport_width - (self.crop.left + self.crop.right)) * -1)

        self.obs.set_filter_properties(self.scene, self.move_filter_name,
                                     pos={"x": new_x, "x_sign": "", "y": new_y, "y_sign": ""},
                                    scale = {"x": zoom_factor, "x_sign": "", "y": zoom_factor, "y_sign": ""})
        self.obs.toggle_filter(self.scene, self.move_filter_name, True)


class EnableFilter(Action):
    def __init__(self, obs: OBS, scene: str, move_filter_name: str):
        self.obs = obs
        self.scene = scene
        self.move_filter_name = move_filter_name

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.obs.toggle_filter(self.scene, self.move_filter_name, True)


class DisableFilter(Action):
    def __init__(self, obs: OBS, scene: str, move_filter_name: str):
        self.obs = obs
        self.scene = scene
        self.move_filter_name = move_filter_name

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.obs.toggle_filter(self.scene, self.move_filter_name, False)


class ChangeVerticalScene(Action):
    def __init__(self, obs: OBS, name: str):
        self.name = name
        self.obs = obs

    def __call__(self, scene: KeyScene, key: OBSKey, click: ClickType):
        self.obs.call_vendor("aitum-vertical-canvas", "switch_scene", {"scene": self.name})