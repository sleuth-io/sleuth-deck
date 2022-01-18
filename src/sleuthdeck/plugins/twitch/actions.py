from os import path
from os.path import dirname
from time import sleep
from typing import List
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from sleuthdeck.colors import Color
from sleuthdeck.deck import Action
from sleuthdeck.deck import ClickType
from sleuthdeck.deck import Key
from sleuthdeck.deck import KeyScene
from sleuthdeck.deck import Updatable
from sleuthdeck.keys import detect_windows_toggle
from sleuthdeck.keys import IconKey
from sleuthdeck.windows import get_window


class TwitchKey(IconKey, Updatable):
    def __init__(
        self,
        profile_dir: str,
        actions: List[Action] = None,
        dark_mode: bool = True,
        **kwargs,
    ):
        super().__init__(
            path.join(dirname(__file__), "assets", "twitch-logo.png"),
            actions=actions,
            **kwargs,
        )
        self._driver: Optional[WebDriver] = None
        self.dark_mode = dark_mode
        self._profile_dir = profile_dir
        self._original_actions = list(actions)

    @property
    def driver(self):
        if not self._driver:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_argument(f"user-data-dir={self._profile_dir}")
            if self.dark_mode:
                options.add_argument("--force-dark-mode")
            self._driver = webdriver.Chrome(chrome_options=options)
        return self._driver

    def reset_driver(self):
        if self._driver:
            self._driver.close()
        self._driver = None

    def connect(self, scene: KeyScene):
        super().connect(scene)

    async def start(self):
        await detect_windows_toggle(
            "Twitch - Google Chrome",
            on_opened=self._on_opened,
            on_closed=self._on_closed,
        )

    def _on_opened(self):
        self.image = IconKey.load_image(
            self._scene.deck,
            self._image_file,
            f"{self._text} (ON)",
            background_color="red",
        )
        self._scene.update_image(self)
        self.actions.clear()
        self.actions.append(CloseChatAction())

    def _on_closed(self):
        self.image = IconKey.load_image(self._scene.deck, self._image_file, self._text)
        self._scene.update_image(self)
        self.actions.clear()
        self.actions.extend(self._original_actions)


class OpenChat(Action):
    def __init__(self, channel: str, hide_header: bool = False):
        self.channel = channel
        self.hide_header = hide_header

    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        driver: WebDriver = key.driver
        driver.get(f"https://www.twitch.tv/popout/{self.channel}/chat?popout=")

        if self.hide_header:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "hMQljH"))
            )
            driver.execute_script(
                """
               var l = document.getElementsByClassName("Layout-sc-nxg1ff-0 hMQljH")[0];
               l.parentNode.removeChild(l);
            """
            )

        for _ in range(3 * 10):
            callouts = driver.find_elements(By.CLASS_NAME, "tw-callout__close")
            for callout in callouts:
                callout.click()
            sleep(0.1)


class CloseChatAction(Action):
    def execute(self, scene: KeyScene, key: Key, click: ClickType):
        window = get_window("Twitch - Google Chrome")
        if window:
            key.reset_driver()
        else:
            print("No chat to close")
