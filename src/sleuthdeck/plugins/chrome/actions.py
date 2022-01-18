from os import path
from os.path import dirname
from typing import List
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.keys import IconKey


class ChromeKey(IconKey):
    def __init__(self, actions: List[Action] = None):
        super().__init__(
            path.join(dirname(__file__), "assets", "Google-Chrome-icon.png"),
            actions=actions,
        )
        self._driver: Optional[WebDriver] = None

    @property
    def driver(self):
        if not self._driver:
            try:
                print("loading chrome")
                options = webdriver.ChromeOptions()
                options.add_experimental_option("useAutomationExtension", False)
                options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"]
                )
                print("starting)")
                self._driver = webdriver.Chrome(chrome_options=options)
            except Exception as e:
                print(f"exception: {e}")
        return self._driver

    def connect(self, scene: KeyScene):
        super().connect(scene)


class OpenWebsite(Action):
    def __init__(self, url: str):
        self._url = url

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        key.driver.get(self._url)
