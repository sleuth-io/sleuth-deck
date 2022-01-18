import os
from functools import partial

from sleuthdeck.actions import MaximizeWindow
from sleuthdeck.actions import MoveWindow
from sleuthdeck.actions import SendHotkey, Command, CloseWindow, Pause
from sleuthdeck.deck import Deck
from sleuthdeck.keys import IconKey
from sleuthdeck.plugins import sound
from sleuthdeck.plugins import twitch
from sleuthdeck.plugins import zoom
from sleuthdeck.plugins.obs.actions import OBSKey, OBS
from sleuthdeck.plugins.twitch.actions import TwitchKey
from sleuthdeck.windows import By

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")


def run(deck: Deck):
    deck.stream_deck.set_brightness(70)
    scene1 = deck.new_key_scene()
    intro = deck.new_video_scene(
        os.path.join(ASSETS_PATH, "intro.mpg"),
        on_finish=lambda: deck.change_scene(scene1),
    )
    obs = OBS(password=os.getenv("OBS_PASSWORD"))

    Key = partial(IconKey, base_path=ASSETS_PATH)
    scene1.add(
        (0, 0),
        zoom.StartMeetingKey(
            text="OM",
            actions=[
                Command("gtk-launch", "obs-zoom"),
                zoom.StartMeeting("https://sleuth-io.zoom.us/j/82836110226"),
                MoveWindow("Zoom Meeting", "9000", 0, 100, 100),
                MaximizeWindow("Zoom Meeting"),
                Pause(1),
                SendHotkey("Zoom Meeting", "alt", "v"),
            ],
            close_actions=[
                zoom.EndMeeting(),
                CloseWindow(By.window_class("obs.obs")),
                SendHotkey(By.title("Exit OBS?"), "tab"),
                SendHotkey(By.title("Exit OBS?"), "enter")
            ]
        ),
    )

    scene1.add(
        (1, 0),
        TwitchKey(text="Stream",
                  profile_dir="/home/mrdon/.config/google-chrome",
                  actions=[
                      Command("gtk-launch", "obs-twitch"),
                      twitch.OpenChat(channel="mrdonbrown", hide_header=True),
                      MoveWindow("Twitch - Google Chrome", "9000", 0, 100, 100),
                      MaximizeWindow("Twitch - Google Chrome"),
                      Pause(2),
                      SendHotkey(By.title("Twitch - Google Chrome"), "f11"),
                      obs.change_scene("Coding - Webcam"),
                  ]),
    )

    scene1.add(
        (1, 1),
        OBSKey(text="Webcam", actions=[obs.change_scene("Coding - Webcam")]),
    )
    scene1.add(
        (1, 2),
        OBSKey(text="Pycharm", actions=[obs.change_scene("Coding - Pycharm")]),
    )
    scene1.add(
        (1, 3),
        OBSKey(text="Firefox", actions=[obs.change_scene("Coding - Firefox")]),
    )
    scene1.add(
        (2, 0),
        Key(
            "Elephant_Walking_animated.gif",
            text="Rimshot",
            actions=[sound.Play("/home/mrdon/dev/twitch/sounds/rimshot.mp3", gain=-30)],
        ),
    )

    # scene1.set_key(0, sleuth.RepoLockKey(project="sleuth", deployment="application"))
    intro.activate()
