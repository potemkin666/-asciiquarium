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


def test_cull_policy_kill_above_y() -> None:
    """Sprite is despawned exactly when ``y < cull_y``."""
    scene = Scene(20, 20)
    s = Sprite(art=".", x=5, y=10.0, vy=-5.0, cull_policy="kill_above_y", cull_y=8.0)
    scene.add(s)
    # First tick: y becomes 9.0 -> still >= cull_y, alive.
    scene.update(0.2)
    assert s in scene.sprites
    assert s.alive
    # Next tick: y becomes 8.0 -> still not strictly less, alive.
    scene.update(0.2)
    assert s.alive
    # Third tick: y becomes 7.0 -> y < cull_y, culled.
    scene.update(0.2)
    assert s not in scene.sprites
    assert not s.alive


def test_cull_policy_kill_below_y() -> None:
    scene = Scene(20, 20)
    s = Sprite(art=".", x=5, y=0.0, vy=2.0, cull_policy="kill_below_y", cull_y=5.0)
    scene.add(s)
    scene.update(1.0)  # y=2.0, alive
    assert s.alive
    scene.update(2.0)  # y=6.0, killed (>= cull_y)
    assert not s.alive
    assert s not in scene.sprites


def test_cull_policy_wrap_x_wraps_off_right_edge() -> None:
    scene = Scene(20, 10)
    s = Sprite(art="o", x=19.0, y=5.0, vx=3.0, cull_policy="wrap_x")
    scene.add(s)
    scene.update(1.0)
    # After update, x=22 -> x0 (=22) > grid width (=20) -> wrap by setting
    # x = -sprite.width (= -1 for a 1-glyph sprite), placing the sprite
    # just off the left edge so it sweeps back in.
    assert s.alive
    assert s in scene.sprites
    assert s.x == -1.0


def test_cull_policy_wrap_x_wraps_off_left_edge() -> None:
    scene = Scene(20, 10)
    s = Sprite(art="o", x=0.0, y=5.0, vx=-2.0, cull_policy="wrap_x")
    scene.add(s)
    scene.update(1.0)
    # After update, x=-2 -> x1 (=-1) < 0 -> wrap by setting x = grid width,
    # placing the sprite just off the right edge so it sweeps back in.
    assert s.alive
    assert s.x == 20.0


def test_cull_policy_wrap_x_still_killed_when_off_vertically() -> None:
    scene = Scene(20, 10)
    s = Sprite(art="o", x=5.0, y=20.0, cull_policy="wrap_x")
    scene.add(s)
    scene.update(0.01)
    assert not s.alive


def test_scene_max_sprites_caps_unprotected_spawns() -> None:
    scene = Scene(20, 10, max_sprites=3)
    scene.add(Sprite(art="a", tag="bubble"))
    scene.add(Sprite(art="b", tag="bubble"))
    scene.add(Sprite(art="c", tag="bubble"))
    # Adding a 4th unprotected sprite should evict the oldest.
    fourth = Sprite(art="d", tag="bubble")
    scene.add(fourth)
    live = [s for s in scene.sprites if s.alive]
    assert len(live) <= 3
    assert fourth.alive
    # The first-added sprite should have been evicted.
    arts = [s.art for s in live]
    assert "a" not in arts


def test_scene_max_sprites_protects_decor_and_fish() -> None:
    scene = Scene(20, 10, max_sprites=2)
    fish = scene.add(Sprite(art="F", tag="fish"))
    castle = scene.add(Sprite(art="C", tag="castle"))
    # No room for a particle, and nothing to evict -> refuse the add.
    bubble = Sprite(art=".", tag="bubble")
    scene.add(bubble)
    assert fish.alive
    assert castle.alive
    assert not bubble.alive
    assert bubble not in scene.sprites


def test_scene_max_sprites_evicts_oldest_unprotected_before_dropping() -> None:
    scene = Scene(20, 10, max_sprites=2)
    scene.add(Sprite(art="F", tag="fish"))  # protected
    bubble1 = scene.add(Sprite(art=".", tag="bubble"))
    # Cap reached. New bubble should evict bubble1 (oldest non-protected).
    bubble2 = Sprite(art=".", tag="bubble")
    scene.add(bubble2)
    assert not bubble1.alive
    assert bubble2.alive
