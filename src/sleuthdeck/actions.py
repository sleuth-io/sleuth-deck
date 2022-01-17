import subprocess

from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Scene


class Command(Action):
    def __init__(self, command: str, *args: str):
        self.command = command
        self.args = args

    def execute(self, scene: KeyScene, click: ClickType):
        print(f"Running {self.command} {' '.join(self.args)}")
        subprocess.run([self.command] + list(self.args))


class ChangeScene(Action):
    def __init__(self, scene: Scene):
        self.scene = scene

    def execute(self, scene: KeyScene, click: ClickType):
        scene.deck.change_scene(self.scene)


class PreviousScene(Action):
    def execute(self, scene: KeyScene, click: ClickType):
        scene.deck.previous_scene()


class Close(Action):
    def execute(self, scene: KeyScene, click: ClickType):
        scene.deck.close()
