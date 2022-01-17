import itertools
import threading
import time
from fractions import Fraction

from PIL import Image
from PIL import ImageSequence
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError


class Animations:
    def __init__(self, deck, fps: int = 30):
        self.deck = deck
        self.fps = fps
        self._frames = {}
        self._thread = threading.Thread(target=self._animate)

    def add(self, key: int, image: Image):
        frames = create_animation_frames(self.deck, image)
        self._frames[key] = frames

    def clear(self, key: int):
        if key in self._frames:
            del self._frames[key]

    def start(self):
        self._thread.start()

    # Helper function that will run a periodic loop which updates the
    # images on each key.
    def _animate(self):
        # Convert frames per second to frame time in seconds.
        #
        # Frame time often cannot be fully expressed by a float type,
        # meaning that we have to use fractions.
        frame_time = Fraction(1, self.fps)

        # Get a starting absolute time reference point.
        #
        # We need to use an absolute time clock, instead of relative sleeps
        # with a constant value, to avoid drifting.
        #
        # Drifting comes from an overhead of scheduling the sleep itself -
        # it takes some small amount of time for `time.sleep()` to execute.
        next_frame = Fraction(time.monotonic())

        # Periodic loop that will render every frame at the set FPS until
        # the StreamDeck device we're using is closed.
        while self.deck.is_open():

            if self._frames:
                try:
                    # Use a scoped-with on the deck to ensure we're the only
                    # thread using it right now.
                    with self.deck:
                        # Update the key images with the next animation frame.
                        for key, frames in dict(self._frames).items():
                            self.deck.set_key_image(key, next(frames))
                except TransportError as err:
                    print("TransportError: {0}".format(err))
                    # Something went wrong while communicating with the device
                    # (closed?) - don't re-schedule the next animation frame.
                    break

            # Set the next frame absolute time reference point.
            #
            # We are running at the fixed `fps`, so this is as simple as
            # adding the frame time we calculated earlier.
            next_frame += frame_time

            # Knowing the start of the next frame, we can calculate how long
            # we have to sleep until its start.
            sleep_interval = float(next_frame) - time.monotonic()

            # Schedule the next periodic frame update.
            #
            # `sleep_interval` can be a negative number when current FPS
            # setting is too high for the combination of host and
            # StreamDeck to handle. If this is the case, we skip sleeping
            # immediately render the next frame to try to catch up.
            if sleep_interval >= 0:
                time.sleep(sleep_interval)


# Loads in a source image, extracts out the individual animation frames (if
# any) and returns an infinite generator that returns the next animation frame,
# in the StreamDeck device's native image format.
def create_animation_frames(deck, icon: Image):
    icon_frames = list()

    # Iterate through each animation frame of the source image
    for frame in ImageSequence.Iterator(icon):
        # Create new key image of the correct dimensions, black background.
        frame_image = PILHelper.create_scaled_image(deck, frame)

        # Pre-convert the generated image to the native format of the StreamDeck
        # so we don't need to keep converting it when showing it on the device.
        native_frame_image = PILHelper.to_native_format(deck, frame_image)

        # Store the rendered animation frame for later user.
        icon_frames.append(native_frame_image)

    # Return an infinite cycle generator that returns the next animation frame
    # each time it is called.
    return itertools.cycle(icon_frames)
