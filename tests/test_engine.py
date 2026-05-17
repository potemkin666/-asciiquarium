from asciiquarium.colors import DEFAULT_FG
from asciiquarium.engine import Grid, Scene, Sprite


def test_grid_put_and_clear() -> None:
    g = Grid(5, 3)
    g.put(1, 1, "X", (10, 20, 30))
    assert g.get(1, 1) == "X"
    assert g.colors[1][1] == (10, 20, 30)
    g.clear()
    assert g.get(1, 1) == " "
    assert g.colors[1][1] == DEFAULT_FG


def test_grid_put_out_of_bounds_is_no_op() -> None:
    g = Grid(3, 3)
    g.put(-1, 0, "X", DEFAULT_FG)
    g.put(0, 10, "X", DEFAULT_FG)
    # Nothing changed.
    assert all(ch == " " for row in g.chars for ch in row)


def test_sprite_dimensions_and_bbox() -> None:
    s = Sprite(art="abc\nde", x=2.0, y=1.0)
    assert s.width == 3
    assert s.height == 2
    assert s.bbox() == (2, 1, 5, 3)


def test_sprite_draw_respects_transparency() -> None:
    s = Sprite(art="a b", mask="rrr", x=0, y=0)
    g = Grid(3, 1)
    s.draw(g)
    assert g.get(0, 0) == "a"
    assert g.get(1, 0) == " "  # transparent space preserved
    assert g.get(2, 0) == "b"


def test_sprite_update_moves_by_velocity() -> None:
    s = Sprite(art="o", x=0.0, y=0.0, vx=2.0, vy=-1.0)
    s.update(0.5)
    assert s.x == 1.0
    assert s.y == -0.5


def test_sprite_offscreen_detection() -> None:
    s = Sprite(art="o", x=-10, y=0)
    assert s.is_offscreen(20, 10) is True
    s.x = 5
    assert s.is_offscreen(20, 10) is False


def test_sprite_covers() -> None:
    s = Sprite(art="ab\n c", x=1, y=1)
    assert s.covers(1, 1) is True
    assert s.covers(2, 2) is True
    assert s.covers(1, 2) is False  # transparent space
    assert s.covers(0, 0) is False  # outside


def test_scene_culls_offscreen_sprites_and_invokes_on_remove() -> None:
    removed = []

    def cb(spr: Sprite) -> None:
        removed.append(spr)

    scene = Scene(10, 5)
    s = Sprite(art="o", x=-5, y=0, vx=-1.0, on_remove=cb)
    scene.add(s)
    scene.update(0.1)
    assert s not in scene.sprites
    assert removed == [s]


def test_scene_render_z_ordering() -> None:
    """Lower depth wins over higher depth at the same cell."""
    scene = Scene(3, 1)
    back = Sprite(art="B", x=0, y=0, depth=10, tag="back")
    front = Sprite(art="F", x=0, y=0, depth=1, tag="front")
    scene.add(back)
    scene.add(front)
    g = Grid(3, 1)
    scene.render(g)
    assert g.get(0, 0) == "F"
