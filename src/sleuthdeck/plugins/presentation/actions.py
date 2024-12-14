from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from typing import Optional, List

import yaml
from obsws_python.error import OBSSDKError
from slugify import slugify

from sleuthdeck.deck import Action, KeyScene, Key, ClickType
from sleuthdeck.plugins.obs import OBS


@dataclass
class Event:
    title: str
    sections: List[Section]
    id: Optional[str] = None

    @property
    def slug(self):
        return slugify(self.title)


@dataclass
class Section:
    title: str
    byline: str
    scene: str | None


class Presentation:
    def __init__(self, obs: OBS, path: str, title_scene_item="Section title",
                byline_scene_item="Section byline",
                 title_scene="Title", overlay_scene="Overlay",
                 guest1_name_item="Guest 1a",
                 guest1_title_item="Guest 1b",
                 guest2_name_item="Guest 2a",
                 guest2_title_item="Guest 2b"
                 ):
        self.path = path
        self.obs = obs
        self.guest1_name_item = guest1_name_item
        self.guest1_title_item = guest1_title_item
        self.guest2_name_item = guest2_name_item
        self.guest2_title_item = guest2_title_item

        self.current_section_idx = 0
        try:
            self._reload()
        except ConnectionError:
            return

        if not self.event.sections:
            return

        self.title_scene_item = title_scene_item
        self.byline_scene_item = byline_scene_item
        self.title_scene = title_scene
        self.overlay_scene = overlay_scene
        self._recording = False

    def _reload(self):
        with open(self.path, "r") as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                self.event = Event("Missing", [])
        sections = []
        if "sections" in data:
            sections = [Section(title=s["title"], byline=s["byline"], scene=s.get("scene")) for s in data["sections"]]

        if "guest1" in data:
            try:
                self.obs.set_item_property(self.guest1_name_item, "text", data["guest1"]["name"])
                self.obs.set_item_property(self.guest1_title_item, "text", data["guest1"]["title"])
            except OBSSDKError:
                print("Error resetting guest labels")

        if "guest2" in data:
            try:
                self.obs.set_item_property(self.guest2_name_item, "text", data["guest2"]["name"])
                self.obs.set_item_property(self.guest2_title_item, "text", data["guest2"]["title"])
            except OBSSDKError:
                print("Error resetting guest labels")

        self.event = Event(
            title=data["title"],
            sections=sections,
        )

    def next_section(self) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            section = self._next_section()

            self._update_labels(section, next_scene=section.scene)
            self.obs.create_record_chapter(section.title)

        return action

    def reset(self, reload: bool = True) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            if reload:
                self._reload()
            self.current_section_idx = 0
            self._update_labels(self.event.sections[0])
            self.obs.create_record_chapter(self.event.sections[self.current_section_idx].title)

        return action

    def toggle_record(self) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            if self._recording:
                self.obs.stop_recording(vertical=True)
                self._recording = False
            else:
                self.obs.start_recording(vertical=True)
                self._recording = True

        return action

    def previous_section(self) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            section = self._previous_section()
            self._update_labels(section, next_scene=section.scene)
            self.obs.create_record_chapter(section.title)

        return action

    def _update_labels(self, section, next_scene: str | None = False):
        self.obs.set_scene_item_enabled(self.overlay_scene, self.title_scene_item, False)
        self.obs.set_scene_item_enabled(self.overlay_scene, self.byline_scene_item, False)
        self.obs.set_item_property(self.title_scene_item, "text", section.title)
        self.obs.set_item_property(self.byline_scene_item, "text", section.byline)
        if next_scene:
            self.obs.call("SetCurrentProgramScene", {"sceneName": next_scene})
            sleep(.3)
        self.obs.set_scene_item_enabled(self.overlay_scene, self.title_scene_item, True)
        self.obs.set_scene_item_enabled(self.overlay_scene, self.byline_scene_item, True)

    def _next_section(self) -> Section:
        if len(self.event.sections) - 1 == self.current_section_idx:
            self.current_section_idx = 0
        else:
            self.current_section_idx += 1

        return self.event.sections[self.current_section_idx]

    def _previous_section(self) -> Section:
        if self.current_section_idx == 0:
            self.current_section_idx = len(self.event.sections) - 1
        else:
            self.current_section_idx -= 1

        return self.event.sections[self.current_section_idx]
