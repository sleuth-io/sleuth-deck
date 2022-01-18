import re
import time
from typing import List
from typing import Optional

from sleuthdeck import shell


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

    def close(self):
        shell.run("wmctrl", "-ic", self.window_id)

    def move(self, x: int, y: int, width: int, height: int):
        shell.run("wmctrl", "-ir", self.window_id, "-e", f"0,{x},{y},{width},{height}")


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
                title=title,
                window_class=window_class,
                desktop_id=desktop_id,
            )
        )
    return result


def get_window(title: str, attempts: int = 1) -> Optional[Window]:
    for attempt in range(attempts):
        for window in get_windows():
            if window.title == title:
                return window
        time.sleep(0.1)

    return None
