from __future__ import annotations
import re
import time
from typing import List, Callable, Union
from typing import Optional

from sleuthdeck import shell


class By:

    def __init__(self, selector: Callable[[Window], bool], repr: str):
        self._selector = selector
        self._repr = repr

    def __call__(self, window: Window):
        return self._selector(window)

    def __repr__(self):
        return self._repr

    @classmethod
    def title(cls, title: str):
        return By(lambda w: w.title == title, f"by.title='{title}'")

    @classmethod
    def window_class(cls, name: str):
        return By(lambda w: w.window_class == name, f"by.window_class='{name}'")


class Window:
    def __init__(self, desktop_id: str, window_class: str, window_id: str, title: str):
        self.desktop_id = desktop_id
        self.window_class = window_class
        self.window_id = window_id
        self.title = title

    def maximize(self):
        shell.run(
            "wmctrl", "-ir", self.window_id, "-b", "add,maximized_vert,maximized_horz"
        )

    def unmaximize(self):
        shell.run(
            "wmctrl", "-ir", self.window_id, "-b", "remove,maximized_vert"
        )

    def close(self):
        shell.run("wmctrl", "-ic", self.window_id)

    def move(self, x: int, y: int, width: int, height: int):
        shell.run("wmctrl", "-ir", self.window_id, "-e", f"0,{x},{y},{width},{height}")

    def focus(self):
        shell.run("wmctrl", "-ia", self.window_id)


    def __repr__(self):
        return f"Window (id='{self.window_id}', class='{self.window_class}', title='{self.title}')"


def get_windows() -> List[Window]:
    output = shell.run("wmctrl", "-lx")
    return _parse_window_output(output)


def _parse_window_output(output):
    result: List[Window] = []
    guessed_host = None
    for line in (l for l in output.split("\n") if l):
        if guessed_host is None:
            window_id, desktop_id, window_class, host, *title = re.split(r"[ ]+", line)
            guessed_host = host
        else:
            idx = line.index(guessed_host)
            window_id, desktop_id, *window_class = re.split(r"[ ]+", line[:idx])
            window_class = " ".join(window_class)
            host, *title = re.split(r"[ ]+", line[idx:])
        title = " ".join(title)
        result.append(
            Window(
                window_id=window_id,
                title=title.strip(),
                window_class=window_class.strip(),
                desktop_id=desktop_id,
            )
        )
    return result


def get_window(selector: Union[str, By], attempts: int = 1) -> Optional[Window]:
    if isinstance(selector, str):
        actual_selector = By.title(selector)
    else:
        actual_selector = selector
    for attempt in range(attempts):
        for window in get_windows():
            if actual_selector(window):
                return window
        time.sleep(0.1)

    print(f"No windows found for {actual_selector}: {get_windows()}")
    return None
