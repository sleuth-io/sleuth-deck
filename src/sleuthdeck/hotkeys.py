from collections import defaultdict

from pynput.mouse import Listener


class Hotkeys:

    def __init__(self):
        self.listener = None
        self.mouse_button_registry = defaultdict(list)
        self.listener = Listener(on_click=self.on_click)

    def start(self):
        self.listener.start()
        self.listener.wait()

    def on_click(self, x, y, button, pressed):
        if pressed:
            for callback in self.mouse_button_registry[button]:
                callback(x, y, button)

    def register_mouse_button(self, button, callback):
        self.mouse_button_registry[button].append(callback)

    def reset(self):
        self.mouse_button_registry.clear()

    def stop(self):
        self.listener.stop()