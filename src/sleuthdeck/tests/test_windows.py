from sleuthdeck.windows import _parse_window_output


def test_parse_window_output():
    output = """
0x06600006  0 obs.obs               mrdon-home OBS 27.0.1+dfsg1-1 (linux) - Profile: Untitled - Scenes: Untitled
0x08000003  0 google-chrome (/home/mrdon/.config/google-chrome).Google-chrome  mrdon-home Twitch - Google Chrome
"""
    windows = _parse_window_output(output)
    assert 2 == len(windows)

    assert {
        "Twitch - Google Chrome",
        "OBS 27.0.1+dfsg1-1 (linux) - Profile: Untitled - Scenes: Untitled",
    } == set(w.title for w in windows)
