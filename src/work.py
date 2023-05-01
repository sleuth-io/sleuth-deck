import os
from functools import partial
from os.path import dirname

from sleuthdeck.actions import MaximizeWindow, Toggle, UnMaximizeWindow, DeckBrightness, Sequential, ChangeScene, \
    PreviousScene, Wait
from sleuthdeck.actions import MoveWindow
from sleuthdeck.actions import SendHotkey, Command, CloseWindow, Pause
from sleuthdeck.deck import Deck, KeyScene
from sleuthdeck.keys import IconKey, FontAwesomeKey
from sleuthdeck.plugins import sound
from sleuthdeck.plugins import twitch
from sleuthdeck.plugins import zoom
from sleuthdeck.plugins.obs.actions import OBSKey, OBS, ObsAction
from sleuthdeck.plugins.presentation.actions import Presentation
from sleuthdeck.plugins.twitch.actions import TwitchKey
from sleuthdeck.windows import By

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")


def run(deck: Deck):
    deck.stream_deck.set_brightness(70)
    scene1 = deck.new_key_scene()
    stream_scene = deck.new_key_scene()
    webinar1_scene = deck.new_key_scene()
    webinar2_scene = deck.new_key_scene()
    intro = deck.new_video_scene(
        os.path.join(ASSETS_PATH, "intro.mpg"),
        on_finish=lambda: deck.change_scene(scene1),
    )
    obs = OBS(password=os.getenv("OBS_PASSWORD"))
    presso = Presentation(obs, "../sleuth-tv-live-s02e03.yml",
                          title_scene_item="Title",
                          byline_scene_item="Byline",
                          title_scene="Me full (title)",
                          overlay_scene="[Scene] Lower-third (labels)")

    build_webinar1_scene(obs, presso, scene1, webinar1_scene)
    build_webinar2_scene(obs, presso, scene1, webinar2_scene)
    build_stream_scene(obs, scene1, stream_scene)

    scene1.add(
        (0, 0),
        zoom.StartMeetingKey(
            text="OM",
            actions=[
                obs.close(),
                Command("gtk-launch", "obs-zoom"),
                zoom.StartMeeting("https://sleuth-io.zoom.us/j/82836110226"),
                Pause(2),
                UnMaximizeWindow("Zoom Meeting"),
                MoveWindow("Zoom Meeting", "6000", 0, 100, 100),
                MaximizeWindow("Zoom Meeting"),
                Pause(3),
                SendHotkey("Zoom Meeting", "alt", "v"),
            ],
            close_actions=[
                zoom.EndMeeting(),
                obs.close()

            ]
        ),
    )

    scene1.add(
        (0, 1),
        zoom.StartMeetingKey(
            text="Zoom",
            actions=[
                obs.close(),
                Command("gtk-launch", "obs-zoom"),
                UnMaximizeWindow("Zoom Meeting"),
                MoveWindow("Zoom Meeting", "6000", 0, 100, 100),
                MaximizeWindow("Zoom Meeting"),
                Pause(3),
                SendHotkey("Zoom Meeting", "alt", "v"),
            ],
            close_actions=[
                zoom.EndMeeting(),
                obs.close()

            ]
        ),
    )

    scene1.add(
        (0, 3),
        OBSKey(text="Forward", actions=[obs.change_scene("Camera only (zoomed)")]),
    )
    scene1.add(
        (0, 4),
        OBSKey(text="Leaned", actions=[obs.change_scene("Camera only (leaned back)")]),
    )

    scene1.add(
        (1, 0),
        IconKey(
            os.path.join(dirname(__file__), "sleuthdeck", "plugins", "twitch", "assets", "twitch-logo.png"),
            text="Stream",
            actions=[ChangeScene(stream_scene)]
        ),
    )

    scene1.add(
        (1, 1),
        IconKey(
            os.path.join(dirname(__file__), "sleuthdeck", "plugins", "twitch", "assets", "twitch-logo.png"),
            text="Webinar 1",
            actions=[ChangeScene(webinar1_scene)]
        ),
    )

    scene1.add(
        (1, 2),
        IconKey(
            os.path.join(dirname(__file__), "sleuthdeck", "plugins", "twitch", "assets", "twitch-logo.png"),
            text="Webinar 2",
            actions=[ChangeScene(webinar2_scene)]
        ),
    )

    scene1.add(
        (1, 3),
        FontAwesomeKey("solid/camera", text="preview", actions=[
            ObsAction(obs, lambda obs_: obs.call("OpenVideoMixProjector", {
                "videoMixType": "OBS_WEBSOCKET_VIDEO_MIX_TYPE_PREVIEW",
                "monitorIndex": 0,
                }))
        ])
    )

    scene1.add(
        (1, 4),
        FontAwesomeKey("solid/camera", text="Section", actions=[Command("flameshot", "gui")]),
    )

    scene1.add(
        (2, 0),
        FontAwesomeKey(name="regular/file-audio", tint="green", actions=[
            SendHotkey("Spotify", "space"),
        ]),
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



    # scene1.set_key(0, sleuth.RepoLockKey(project="sleuth", deployment="application"))
    intro.activate()


def build_stream_scene(obs, scene1, stream_scene):
    stream_scene.add(
        (0, 0),
        OBSKey(text="Webcam", actions=[obs.change_scene("Coding - Webcam")]),
    )
    # stream_scene.add(
    #     (0, 1),
    #     OBSKey(text="Side PC", actions=[obs.change_scene("Coding - Side PC")]),
    # )
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
                      obs.close(),
                      Command("gtk-launch", "obs-twitch"),
                      twitch.OpenChat(channel="mrdonbrown", hide_header=True),
                      MoveWindow("mrdondown - Chat - Twitch", "6000", 0, 100, 100),
                      MaximizeWindow("mrdondown - Chat - Twitch"),
                      Pause(5),
                      SendHotkey(By.title("mrdondown - Chat - Twitch"), "f11"),
                      obs.change_scene("Coding - Webcam"),
                      ChangeScene(stream_scene)
                  ]),
    )
    stream_scene.add(
        (2, 4),
        FontAwesomeKey("regular/circle-stop",
                       text="Exit",
                       actions=[ChangeScene(scene1)])
    )


def build_webinar1_scene(obs: OBS, presso: Presentation, parent_scene: KeyScene, webinar_scene: KeyScene):
    _build_webinar_scene_base(obs, parent_scene, presso, webinar_scene)

    webinar_scene.add(
        (2, 0),
        OBSKey(text="Host 2", actions=[obs.change_scene("Me and Guest (local)")]),
    )


def build_webinar2_scene(obs: OBS, presso: Presentation, parent_scene: KeyScene, webinar_scene: KeyScene):
    _build_webinar_scene_base(obs, parent_scene, presso, webinar_scene)

    webinar_scene.add(
        (2, 0),
        OBSKey(text="3 way", actions=[obs.change_scene("Me and 2 Guests")]),
    )

    webinar_scene.add(
        (2, 2),
        OBSKey(text="Guest2", actions=[obs.change_scene("Guest 2 full")]),
    )


def _build_webinar_scene_base(obs, parent_scene, presso, webinar_scene):
    webinar_scene.add(
        (0, 0),
        OBSKey(text="Intro", actions=[presso.reset(),
                                      obs.change_scene("Starting soon"),
                                      Wait(62),
                                      # Wait(5),
                                      obs.start_recording(),
                                      obs.change_scene("Intro video"),
                                      Wait(6),
                                      presso.next_section(),
                                      obs.change_scene("Me full")]),
    )
    webinar_scene.add(
        (0, 1),
        OBSKey(text="Logo", actions=[obs.change_scene("Intro video")]),
    )
    webinar_scene.add(
        (0, 2),
        FontAwesomeKey("regular/flag", text="Reset", actions=[presso.reset()]),
    )
    webinar_scene.add(
        (0, 3),
        FontAwesomeKey("solid/arrow-left", text="Prev", actions=[presso.previous_section(), ]),
        # Pause(3),
        # obs.change_scene("Me full")]),
    )
    webinar_scene.add(
        (0, 4),
        FontAwesomeKey("solid/arrow-right", text="Next", actions=[presso.next_section(), ]),
        # Pause(3),
        # obs.change_scene("Me full")]),
    )
    # webinar_scene.add(
    #     (2, 3),
    #     TwitchKey(text="Start",
    #               profile_dir="/home/mrdon/.config/google-chrome",
    #               actions=[
    #                   obs.close(),
    #                   Command("gtk-launch", "obs-webinar"),
    #                   Command("gtk-launch", "chromium https://www.youtube.com/live_chat?is_popout=1&v=i-Lz4bhUNO8"),
    #                   MoveWindow(By.window_class("chromium.Chromium"), "6000", 0, 100, 100),
    #                   MaximizeWindow(By.window_class("chromium.Chromium"), ),
    #                   Pause(5),
    #                   SendHotkey(By.window_class("chromium.Chromium"), "f11"),
    #                   obs.change_scene("Starting soon"),
    #               ]),
    # )
    webinar_scene.add(
        (1, 0),
        OBSKey(text="Host", actions=[obs.change_scene("Me full")]),
    )
    webinar_scene.add(
        (1, 1),
        OBSKey(text="Host Share", actions=[obs.change_scene("Me screenshare")]),
    )
    webinar_scene.add(
        (1, 2),
        OBSKey(text="Guest 1 share", actions=[obs.change_scene("Guest 1 screenshare")]),
    )
    webinar_scene.add(
        (1, 3),
        FontAwesomeKey("brands/rocketchat", text="Chat", actions=[
            Toggle(on_enable=[obs.toggle_source("Title", False, "[Scene] Lower-third (labels)"),
                              obs.toggle_source("Byline", False, "[Scene] Lower-third (labels)"),
                              obs.toggle_source("Chat highlight", True, "[Scene] Lower-third (labels)"),
                              ],
                   on_disable=[
                       obs.toggle_source("Chat highlight", False, "[Scene] Lower-third (labels)"),
                       obs.toggle_source("Title", True, "[Scene] Lower-third (labels)"),
                       obs.toggle_source("Byline", True, "[Scene] Lower-third (labels)"),

                   ])])
    )
    webinar_scene.add(
        (1, 4),
        FontAwesomeKey("solid/camera", text="T Cam", actions=[obs.toggle_source("[Scene] Me corner (shadowed)"),
                                                              ]),
    )
    webinar_scene.add(
        (2, 1),
        OBSKey(text="Guest1", actions=[obs.change_scene("Guest 1 full")]),
    )
    webinar_scene.add(
        (2, 3),
        OBSKey(text="End", actions=[obs.change_scene("Ending"),
                                    Wait(2),
                                    obs.stop_recording()]),
    )
    webinar_scene.add(
        (2, 4),
        FontAwesomeKey("regular/circle-stop",
                       text="Exit",
                       actions=[ChangeScene(parent_scene)])
    )

