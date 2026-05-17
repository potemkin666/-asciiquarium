from asciiquarium.colors import DEFAULT_FG, color_for


def test_known_codes_map_to_palette() -> None:
    assert color_for("r") != DEFAULT_FG
    assert color_for("W") == (255, 255, 255)


def test_unknown_or_blank_falls_back_to_default() -> None:
    assert color_for("") == DEFAULT_FG
    assert color_for(" ") == DEFAULT_FG
    assert color_for(".") == DEFAULT_FG
    assert color_for("?") == DEFAULT_FG
