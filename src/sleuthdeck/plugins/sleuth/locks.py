import threading
from os import path
from os.path import dirname
from typing import Optional

from sleuthdeck.deck import Key, Deck
from sleuthdeck.plugins.sleuth import Sleuth


class RepositoryLockKey(Key):
    def __init__(self, sleuth: Sleuth, project: str, deployment: Optional[str] = None):
        super().__init__()
        self.sleuth = sleuth
        self.project = project
        self.deployment = deployment
        self._thread = threading.Thread(target=self._update)

    def connect(self, deck: Deck):
        image = path.join(dirname(__file__), "lock.jpg")
        self.image = image
        super().connect(deck)

    def _update(self):
        # todo: add periodic updates from sleuth to update actions and icon
        pass

