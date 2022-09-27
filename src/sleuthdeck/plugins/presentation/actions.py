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


class Presentation:
    def __init__(self, obs: OBS, path: str, title_scene_item="Section title",
                byline_scene_item="Section byline",
                 title_scene="Title", overlay_scene="Overlay",
                 guest_name_item="Guest 1",
                 guest_title_item="Guest 2"):
        self.path = path
        self.obs = obs
        self.guest_name_item = guest_name_item
        self.guest_title_item = guest_title_item

        self._reload()
        if not self.event.sections:
            return

        self.current_section_idx = 0
        self.title_scene_item = title_scene_item
        self.byline_scene_item = byline_scene_item
        self.title_scene = title_scene
        self.overlay_scene = overlay_scene

    def _reload(self):
        with open(self.path, "r") as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                self.event = Event("Missing", [])
        sections = []
        if "sections" in data:
            sections = [Section(title=s["title"], byline=s["byline"]) for s in data["sections"]]

        if "guest" in data:
            try:
                self.obs.set_item_property(self.guest_name_item, "text", data["guest"]["name"])
                self.obs.set_item_property(self.guest_title_item, "text", data["guest"]["title"])
            except OBSSDKError:
                print("Error resetting guest labels")

        self.event = Event(
            title=data["title"],
            sections=sections,
        )

    def next_section(self) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            self._update_labels(self._next_section(), new_scene=False)

        return action

    def reset(self, reload: bool = True) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            if reload:
                self._reload()
            self.current_section_idx = 0
            self._update_labels(self.event.sections[0], new_scene=False)

        return action

    def previous_section(self) -> Action:
        def action(scene: KeyScene, key: Key, click: ClickType):
            self._update_labels(self._previous_section(), new_scene=False)

        return action

    def _update_labels(self, section, new_scene=True):
        self.obs.set_scene_item_enabled(self.overlay_scene, self.title_scene_item, False)
        self.obs.set_scene_item_enabled(self.overlay_scene, self.byline_scene_item, False)
        self.obs.set_item_property(self.title_scene_item, "text", section.title)
        self.obs.set_item_property(self.byline_scene_item, "text", section.byline)
        if new_scene:
            self.obs.change_scene(self.title_scene)
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
