import os
from functools import partial

from sleuthdeck.actions import Action
from sleuthdeck.actions import ChangeScene
from sleuthdeck.actions import Close
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Deck
from sleuthdeck.deck import KeyScene
from sleuthdeck.keys import IconKey
from sleuthdeck.plugins import obs
from sleuthdeck.plugins import zoom
from sleuthdeck.plugins.chrome.actions import ChromeKey
from sleuthdeck.plugins.chrome.actions import OpenWebsite
from sleuthdeck.plugins.obs.actions import OBSKey
from sleuthdeck.plugins.sound import PlaySoundAction
from sleuthdeck.plugins.twitch.actions import OpenChat
from sleuthdeck.plugins.twitch.actions import TwitchKey

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

        Key = partial(IconKey, base_path=ASSETS_PATH)
        scene1.add(0, Key("Pressed.png", text="Blah", actions=[ChangeScene(scene2)]))
        scene1.add(
            1,
            zoom.StartMeetingKey(
                text="OM", url="https://sleuth-io.zoom.us/j/82836110226"
            ),
        )
        scene1.add(
            4,
            Key(
                "Elephant_Walking_animated.gif",
                actions=[
                    PlaySoundAction(
                        "/home/mrdon/dev/twitch/sounds/rimshot.mp3", gain=-30
                    )
                ],
            ),
        )
        scene1.add(
            3,
            TwitchKey(
                profile_dir="/home/mrdon/.config/google-chrome",
                text="Chat",
                actions=[OpenChat(channel="mrdonbrown", hide_header=True)],
            ),
        )

        scene1.add(
            (2, 1),
            OBSKey(
                password="blah", text="Video 1", actions=[obs.ChangeScene("Video 1")]
            ),
        )
        scene1.add(2, Key("Elephant_Walking_animated.gif", actions=[Close()]))

        scene2.add(
            (1, 2), Key("Elephant_Walking_animated.gif", actions=[ChangeScene(scene1)])
        )

        # scene1.set_key(0, sleuth.RepoLockKey(project="sleuth", deployment="application"))

        intro.activate()
