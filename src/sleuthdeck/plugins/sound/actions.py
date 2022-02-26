from pydub import AudioSegment
from pydub.playback import play
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene


class Play(Action):
    def __init__(self, sound_file: str, gain: int = 0):
        sound = AudioSegment.from_file(sound_file)
        sound += gain
        self._sound = sound

    def __call__(self, scene: KeyScene, key: Key, click: ClickType):
        play(self._sound)
