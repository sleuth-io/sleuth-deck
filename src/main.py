import os
from functools import partial

from sleuthdeck.actions import Action
from sleuthdeck.actions import ChangeScene
from sleuthdeck.actions import Close
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Deck
from sleuthdeck.deck import IconKey
from sleuthdeck.deck import KeyScene
from sleuthdeck.plugins import zoom

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")

if __name__ == "__main__":
    deck = Deck()
    with deck:
        scene1 = deck.new_key_scene()
        intro = deck.new_video_scene(
            os.path.join(ASSETS_PATH, "intro.mpg"),
            on_finish=lambda: deck.change_scene(scene1),
        )
        scene2 = deck.new_key_scene()

        class CustomAction(Action):
            def execute(self, scene: KeyScene, click: ClickType):
                print(f"state: {click}")

        Key = partial(IconKey, base_path=ASSETS_PATH)
        scene1.add(0, Key("Pressed.png", text="Blah", actions=[ChangeScene(scene2)]))
        scene1.add(
            1,
            zoom.StartMeetingKey(
                text="OM", url="https://sleuth-io.zoom.us/j/82836110226"
            ),
        )
        scene1.add(4, Key("Elephant_Walking_animated.gif", actions=[CustomAction()]))
        scene1.add(2, Key("Elephant_Walking_animated.gif", actions=[Close()]))

        scene2.add(
            (1, 2), Key("Elephant_Walking_animated.gif", actions=[ChangeScene(scene1)])
        )

        # scene1.set_key(0, sleuth.RepoLockKey(project="sleuth", deployment="application"))

        intro.activate()
