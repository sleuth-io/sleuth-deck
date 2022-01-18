import re
from typing import List
from typing import Optional

from sleuthdeck import shell


class Window:
    def __init__(self, viewport_id: str, window_id: str, title: str):
        self.viewport_id = viewport_id
        self.window_id = window_id
        self.title = title

    def maximize(self):
        shell.run(
            "wmctrl", "-ir", self.window_id, "-b", "add,maximized_vert,maximized_horz"
        )

    def close(self):
        shell.run("wmctrl", "-ic", self.window_id)

    def move_to_desktop(self, target_id):
        shell.run("wmctrl", "-ir", self.window_id, "-t", target_id)


def get_windows() -> List[Window]:
    result: List[Window] = []
    output = shell.run("wmctrl", "-l")
    for line in (l for l in output.split("\n") if l):
        window_id, viewport_id, host, *title = re.split(r"[ ]+", line)
        title = " ".join(title)
        result.append(Window(window_id=window_id, title=title, viewport_id=viewport_id))

    return result


def get_window(title: str) -> Optional[Window]:
    for window in get_windows():
        if window.title == title:
            return window

    return None
