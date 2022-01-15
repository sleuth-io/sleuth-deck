import os

from sleuthdeck.deck import Deck, IconKey

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")

if __name__ == "__main__":
    deck = Deck()
    with deck:
        scene1 = deck.new_key_scene()
        intro = deck.new_video_scene(os.path.join(ASSETS_PATH, "intro.mpg"),
                                     on_finish=lambda: deck.change_scene(scene1))
        scene2 = deck.new_key_scene()


        def on_click(state):
            print(f"state: {state}")


        scene1.add(0, IconKey(os.path.join(ASSETS_PATH, "Pressed.png"), text="Blah",
                              on_click=lambda state: deck.change_scene(scene2)))
        scene1.add(4, IconKey(os.path.join(ASSETS_PATH, "Elephant_Walking_animated.gif"), on_click=on_click))
        scene1.add(2, IconKey(os.path.join(ASSETS_PATH, "Elephant_Walking_animated.gif"),
                              on_click=lambda state: deck.close()))

        scene2.add((1,2), IconKey(os.path.join(ASSETS_PATH, "Elephant_Walking_animated.gif"),
                              on_click=lambda state: deck.change_scene(scene1)))

        # scene1.set_key(0, sleuth.RepoLockKey(project="sleuth", deployment="application"))

        intro.activate()
