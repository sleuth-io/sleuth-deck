import os
from functools import partial
from os.path import dirname

from sleuthdeck.actions import MaximizeWindow, Toggle, UnMaximizeWindow, DeckBrightness, Sequential, ChangeScene, \
    PreviousScene
from sleuthdeck.actions import MoveWindow
from sleuthdeck.actions import SendHotkey, Command, CloseWindow, Pause
from sleuthdeck.deck import Deck
from sleuthdeck.keys import IconKey, FontAwesomeKey
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
    stream_scene = deck.new_key_scene()
    intro = deck.new_video_scene(
        os.path.join(ASSETS_PATH, "intro.mpg"),
        on_finish=lambda: deck.change_scene(scene1),
    )
    obs = OBS(password=os.getenv("OBS_PASSWORD"))

    scene1.add(
        (0, 0),
        zoom.StartMeetingKey(
            text="OM",
            actions=[
                CloseWindow(By.window_class("obs.obs"), wait=0),
                Command("gtk-launch", "obs-zoom"),
                zoom.StartMeeting("https://sleuth-io.zoom.us/j/82836110226"),
                Pause(2),
                UnMaximizeWindow("Zoom Meeting"),
                MoveWindow("Zoom Meeting", "6000", 0, 100, 100),
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
        IconKey(
            os.path.join(dirname(__file__), "sleuthdeck", "plugins", "twitch", "assets", "twitch-logo.png"),
            text="Stream",
            actions=[ChangeScene(stream_scene)]
        ),
    )

    sleep_toggle = Toggle(
            on_enable=DeckBrightness(5),
            on_disable=DeckBrightness(70),
        )
    scene1.add(
        (2, 3),
        FontAwesomeKey(name="regular/moon", tint="blue", actions=[sleep_toggle]),
    )

    scene1.add(
        (2, 4),
        FontAwesomeKey(name="regular/lightbulb", enabled=True, actions=[Toggle(
            on_enable=Sequential(
                Command("/home/mrdon/dev/twitch/lights/on.sh"),
                lambda *args: sleep_toggle(*args)
            ),
            on_disable=Sequential(
                Command("/home/mrdon/dev/twitch/lights/off.sh"),
                lambda *args: sleep_toggle(*args)
            ),
            initial=True)
        ]),
    )


    stream_scene.add(
        (0, 0),
        OBSKey(text="Webcam", actions=[obs.change_scene("Coding - Webcam")]),
    )
    stream_scene.add(
        (0, 1),
        OBSKey(text="Pycharm", actions=[obs.change_scene("Coding - Pycharm")]),
    )
    stream_scene.add(
        (0, 2),
        OBSKey(text="Firefox", actions=[obs.change_scene("Coding - Firefox")]),
    )
    stream_scene.add(
        (0, 3),
        OBSKey(text="Terminal", actions=[obs.change_scene("Coding - Terminal")]),
    )
    stream_scene.add(
        (0, 4),
        OBSKey(text="Gopro", actions=[obs.change_scene("Coding - Gopro")]),
    )
    stream_scene.add(
        (1, 0),
        OBSKey(text="BRB", actions=[obs.change_scene("Coding - Be right back")]),
    )
    stream_scene.add(
        (2, 0),
        FontAwesomeKey("regular/face-grimace",
                       text="Rimshot",
                       actions=[sound.Play("/home/mrdon/dev/twitch/sounds/rimshot.mp3", gain=-13)],
                       ),
    )
    stream_scene.add(
        (2, 1),
        OBSKey(text="Overlays",
               actions=[obs.toggle_source("Chat message callout", False, scene="[Scene] Overlay - Full"),
                        Pause(.3),
                        obs.toggle_source("Section title", True, scene="[Scene] Overlay - Full"),
                        obs.toggle_source("Section byline", True, scene="[Scene] Overlay - Full")]),
    )
    stream_scene.add(
        (2, 2),
        OBSKey(text="Chat", actions=[
            obs.toggle_source("Section title", False, scene="[Scene] Overlay - Full"),
            obs.toggle_source("Section byline", False, scene="[Scene] Overlay - Full"),
            Pause(.3),
            obs.toggle_source("Chat message callout", True, scene="[Scene] Overlay - Full"),
        ]),
    )
    stream_scene.add(
        (2, 3),
        TwitchKey(text="Start",
                  profile_dir="/home/mrdon/.config/google-chrome",
                  actions=[
                      Command("gtk-launch", "obs-twitch"),
                      twitch.OpenChat(channel="mrdonbrown", hide_header=True),
                      MoveWindow("Twitch - Google Chrome", "6000", 0, 100, 100),
                      MaximizeWindow("Twitch - Google Chrome"),
                      Pause(5),
                      SendHotkey(By.title("Twitch - Google Chrome"), "f11"),
                      obs.change_scene("Coding - Webcam"),
                      ChangeScene(stream_scene)
                  ]),
    )
    stream_scene.add(
        (2, 4),
        FontAwesomeKey("regular/circle-stop",
                       text="Exit",
                       actions=[PreviousScene()])
    )

    # scene1.set_key(0, sleuth.RepoLockKey(project="sleuth", deployment="application"))
    intro.activate()
