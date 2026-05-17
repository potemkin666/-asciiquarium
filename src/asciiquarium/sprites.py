"""ASCII art sprites for the aquarium.

Each sprite is exposed as a small dataclass containing the art string and an
optional color mask string of identical shape. Multi-directional sprites
provide both a ``left`` and ``right`` form. Where the original asciiquarium
shipped extensive color masks, we provide compact masks tuned for the
limited palette used here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpriteArt:
    art: str
    mask: str | None = None


@dataclass(frozen=True)
class DirectionalSprite:
    right: SpriteArt
    left: SpriteArt


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

WATERLINE_SEGMENTS: list[str] = [
    "^^^^ ^^^  ^^^   ^^^    ^^^^      ",
    "^^^^      ^^^^     ^^^    ^^     ",
    "^^      ^^^^      ^^^    ^^^^^^  ",
    "^^^^   ^^^^   ^^^  ^^^^   ^^^    ",
]


CASTLE = SpriteArt(
    art=r"""
               T~~
               |
              /^\
             /   \
 _   _   _  /     \  _   _   _
[ ]_[ ]_[ ]/ _   _ \[ ]_[ ]_[ ]
|_=__-_ =_|_[ ]_[ ]_|_=-___-__|
 | _- =  | =_ = _    |= _=   |
 |= -[]  |- = _ =    |=  =__-|
 |=  _   |_-=_[] _   |-_   = |
 |=_ =[  | =_   |=  _|=_[][]_|
 |-  - --|=_ =__|--=_=_-=_=__|
 |=[]_-= _--=_____ =- =-=__-=|
 |- - - = -=____===_- = =_--=|
""",
    mask=r"""
               yyy
               y
              y y
             y   y
 y   y   y  y     y  y   y   y
yyyyyyyyyyyyy y   y yyyyyyyyyyy
yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
 y    y  y   y   y    y   y  y
 y       y     y y     y      y
 y       y      y       y     y
 y    y  y     y    y       y y
 y       y       y    y   y   y
 y       y         y    y     y
 y       y           y    y   y
""",
)


SEAWEED_FRAMES: tuple[str, str] = (
    "(\n )\n(\n )\n(\n )\n(",
    " )\n(\n )\n(\n )\n(\n )",
)


# ---------------------------------------------------------------------------
# Fish (small/medium)
# ---------------------------------------------------------------------------

FISH: list[DirectionalSprite] = [
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
       \
     ...\..,
\  /'       \
 >=     (  ' >
/  \      / /
    `"'"'/''
""",
            mask=r"""
       2
     1112111
2  11       1
 66     7  4 5
2  11      1 1
    11111311
""",
        ),
        left=SpriteArt(
            art=r"""
      /
   ,../...
  /       '\  /
 < '  )     =<
  \ \      /  \
   ``\'"'"'
""",
            mask=r"""
      2
   1112111
  1       11  2
 5 4  7     66
  1 1      11  2
   3111111
""",
        ),
    ),
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
    \
\ /--\
 >=  (o>
/ \__/
    /
""",
            mask=r"""
    2
1 1111
 66  8B
1 1111
    2
""",
        ),
        left=SpriteArt(
            art=r"""
  /
 /--\ /
<o)  =<
 \__/ \
  \
""",
            mask=r"""
  2
 1111 1
B8  66
 1111 1
  2
""",
        ),
    ),
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
       \:.
\;,   ,;\\\,,
  \\\;;:::::::o
  ///;;::::::::<
 /;` ``/////``
""",
            mask=r"""
       222
2222   222222
  GGGGGGGGGGGW
  GGGGGGGGGGGY
 222  222222
""",
        ),
        left=SpriteArt(
            art=r"""
      .:/
   ,,///;,   ,;/
 o:::::::;;///
>::::::::;;\\\
  ''\\\\\'' ';\
""",
            mask=r"""
      222
   222222   2222
 WGGGGGGGGGGG
YGGGGGGGGGGG
  222222  222
""",
        ),
    ),
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
  __
><_'>
   '
""",
            mask=r"""
  11
CC11C
   1
""",
        ),
        left=SpriteArt(
            art=r"""
 __
<'_><
 `
""",
            mask=r"""
 11
C11CC
 1
""",
        ),
    ),
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
   ___
  /o  \/
  \___/\
""",
            mask=r"""
   111
  1Y  11
  11111
""",
        ),
        left=SpriteArt(
            art=r"""
  ___
\/  o\
/\___/
""",
            mask=r"""
  111
11  Y1
111111
""",
        ),
    ),
]


# ---------------------------------------------------------------------------
# Large creatures
# ---------------------------------------------------------------------------

SHARK = DirectionalSprite(
    right=SpriteArt(
        art=r"""
                              __
                             ( `\
  ,??????????????????????????)   `\
;' `.?????????????????????(     `\__
 ;   `.?????????????????__)        `\
  `.   `.____________.'              \
    `-.,-.,-.,-.,-.,-.,-.,-.,-.,-.,-.,>
""",
        mask=r"""
                              ww
                             wwww
  wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww
www www                       wwwwww
 ww   www                  wwww
  www   wwwwwwwwwwwwwwwwww             w
    wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwR
""",
    ),
    left=SpriteArt(
        art=r"""
                     __
                   /' )
                 /'   (??????????????????????????,
              __/     )?????????????????????????.' `;
            /'        (__?????????????????????.'   ;
           /              `.____________.'   .'
          <,-.,-.,-.,-.,-.,-.,-.,-.,-.,-.,-.-'
""",
        mask=r"""
                     ww
                   wwww
                 wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww
              wwwww                       www www
            wwww                  wwww   ww
           w              wwwwwwwwwwwwwwww
          Rwwwwwwwwwwwwwwwwwwwwwwwwwwwwww
""",
    ),
)


SHIP = DirectionalSprite(
    right=SpriteArt(
        art=r"""
     |    |    |
    )_)  )_)  )_)
   )___))___))___)\
  )____)____)_____)\
_____|____|____|____\\__
\                   /
""",
        mask=r"""
     y    y    y
     w    w    w
    wwwwwwwwwwwwww
   wwwwwwwwwwwwwwwww
yyyyyyyyyyyyyyyyyyyyyyy
yyyyyyyyyyyyyyyyyyyyy
""",
    ),
    left=SpriteArt(
        art=r"""
         |    |    |
        (_(  (_(  (_(
      /(___((___((___(
     /(_____(____(____(
__//____|____|____|____
  \                    /
""",
        mask=r"""
         y    y    y
         w    w    w
      wwwwwwwwwwwwwwww
     wwwwwwwwwwwwwwwwww
yyyyyyyyyyyyyyyyyyyyyyy
  yyyyyyyyyyyyyyyyyyyyy
""",
    ),
)


WHALE = DirectionalSprite(
    right=SpriteArt(
        art=r"""
        .-----:
      .'       `.
,????/       (o) \
\`._/          ,__)
""",
        mask=r"""
        BBBBBBB
      BB       BB
WWWWBB       Y B
WWWBBBB        BBBB
""",
    ),
    left=SpriteArt(
        art=r"""
    :-----.
  .'       `.
 / (o)       \????,
(__,          \_.'/
""",
        mask=r"""
    BBBBBBB
  BB       BB
 B Y       BBWWWW
BBBB        BBBBWWW
""",
    ),
)


BIG_FISH = DirectionalSprite(
    right=SpriteArt(
        art=r"""
 ______
`""-.  `````-----.....__
     `.  .      .       `-.
       :     .     .       `.
 ,?????:   .    .          _ :
:??????`._   .    .        (@) `;
`._?????``.   .      .   _ ,'
   `--.??.?`-.______,-'  `'
        `.?`.____
          `-.____`-.
""",
        mask=r"""
 BBBBBB
BBBBBBBBBBBBBBBBBBBBBBBB
     BB  B      B       BBB
       B     B     B       BB
 BBBBBBB   B    B          B B
BBBBBBBBBB   B    B        Y BB
BBBBBBBBBBBB   B      B   B B
   BBBBBBBBBBBBBBBBBBBB  BB
        BBBBBBBB
          BBBBBBBB
""",
    ),
    left=SpriteArt(
        art=r"""
                           ______
                  __.....-----'''''  .-""'
                .-'       .      .  .'
              .'       .     .     :
             : _          .    .   :?????,
            ;' (@)        .    .   _.''????:
              `, _   .      .   .''?????_.'
                  `'  `-.______.-'??.--''
                              ____.'?.'
                            .-'____.-'
""",
        mask=r"""
                           BBBBBB
                  BBBBBBBBBBBBBBBBBBBBBBBB
                BBB       B      B  BB
              BB       B     B     B
             B B          B    B   BBBBBBB
            BB Y        B    B   BBBBBBBBBB
              BB B   B      B   BBBBBBBBBBBB
                  BB  BBBBBBBBBBBBBBBBBBBBBB
                              BBBBBBBB
                            BBBBBBBB
""",
    ),
)


# ---------------------------------------------------------------------------
# Misc.
# ---------------------------------------------------------------------------

BUBBLES: tuple[str, ...] = (".", "o", "O", "O")


# ---------------------------------------------------------------------------
# Japanese-themed sprites
# ---------------------------------------------------------------------------

# Koi (錦鯉 / nishikigoi). Two variants in classic kōhaku-style red+white
# patterns over a dark outline. Color mask uses ``R`` (red), ``W`` (white),
# and ``k`` (black) to evoke the traditional palette.
KOI: list[DirectionalSprite] = [
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
   ___
  /. o\___
 ( o O o )>
  \___,_/
""",
            mask=r"""
   WWW
  WWWWWWWW
 RkRWkRkWk
  WWWWWWW
""",
        ),
        left=SpriteArt(
            art=r"""
     ___
  ___/o .\
 <( o O o )
   \_,___/
""",
            mask=r"""
     WWW
  WWWWWWWW
 kWkRkWRkR
   WWWWWWW
""",
        ),
    ),
    DirectionalSprite(
        right=SpriteArt(
            art=r"""
    _____
   /     \__
  ( o   O   >
   \_,_,_,_/
""",
            mask=r"""
    WWWWW
   WWRRRWWW
  WkWRWRkRR
   WWWWWWWW
""",
        ),
        left=SpriteArt(
            art=r"""
     _____
   __/     \
  <   O   o )
   \_,_,_,_/
""",
            mask=r"""
     WWWWW
   WWWRRRWW
  RRkRWRWkW
   WWWWWWWW
""",
        ),
    ),
]


# Sea turtle. Slow-moving and reasonably large; designed for a rare event.
TURTLE = DirectionalSprite(
    right=SpriteArt(
        art=r"""
        ___..._
   _,--'       "`-.
 ,'.  .   .--.   . `.
/ /|.  . .'    '. . .\
\/_,. . .  .  . . , .|
 \,_|_,.__'__.__,__|/
   _/   |/   \|   \_
""",
        mask=r"""
        gggggggg
   ggggggggggggggg
 ggGgGgggGGGGGgggGgg
ggggGgGgGgGGGGgGgGgg
ggGGggGgGgGgGgGgGggg
 ggggggggggggggggggg
   gggggGgggggGgggg
""",
    ),
    left=SpriteArt(
        art=r"""
        _...__
     .-'       `--._
   .' .   .--.   .  '.
  /. . .'    '. . .|\ \
 |. , . .  .  . .,.\_\/
  \|__,__.__'__,_|_,/
   _/   |/   \|   \_
""",
        mask=r"""
        ggggggg
     gggggggggggggg
   ggggGggGGGGgggGggg
  ggGgGgGGGGGgGgGgggg
 ggGgGgGgGgGgGgGGggGg
  gggggggggggggggggg
   gggggGgggggGgggg
""",
    ),
)


# Sakura (cherry blossom) petals: tiny single-glyph sprites that drift down
# from above the waterline. Multiple petal glyphs and color codes give the
# stream subtle variety.
SAKURA_GLYPHS: tuple[str, ...] = (".", ",", "*", "'", "`")
SAKURA_COLOR_CODES: tuple[str, ...] = ("M", "m", "W", "R")


# Torii gate silhouette, intended to be anchored to the bottom-right corner
# of the scene as a static background element. The mask uses ``r`` so it
# stands out against the water like a traditional vermilion gate.
TORII = SpriteArt(
    art=r"""
 ______________
 \____________/
  |          |
  |==========|
  ||        ||
  ||        ||
  ||        ||
  ||        ||
""",
    mask=r"""
 RRRRRRRRRRRRRR
 RRRRRRRRRRRRRR
  R          R
  RRRRRRRRRRRR
  RR        RR
  RR        RR
  RR        RR
  RR        RR
""",
)


# Bamboo shishi-odoshi (deer-scarer). Two frames: at rest (water filling)
# and tipped (just clacked). The aquarium swaps frames around the audible
# clack so the viewer sees the motion that "caused" the sound.
SHISHI_ODOSHI_REST = SpriteArt(
    art=r"""
   |
   |__
   |  \__
   |     \_
   |
  _|_
""",
    mask=r"""
   g
   ggg
   gggggg
   ggggggg
   g
  ggg
""",
)


SHISHI_ODOSHI_TIPPED = SpriteArt(
    art=r"""
   |
   |
   |__
   |  \__
   |     \
  _|_
""",
    mask=r"""
   g
   g
   ggg
   gggggg
   gggggg
  ggg
""",
)


# Seaweed alternates for ink-wash mode: shaded with the block characters
# ░ ▒ ▓ so it reads as a sumi-e brush stroke rather than line art.
INKWASH_SEAWEED_GLYPHS: tuple[str, str, str] = ("░", "▒", "▓")


# ---------------------------------------------------------------------------
# Rare creatures (Abyssarium)
# ---------------------------------------------------------------------------

# Giant squid: tentacles drifting in the deep mid-water band.
GIANT_SQUID = DirectionalSprite(
    right=SpriteArt(
        art=r"""
       _____
      /     \
     ( O   O )
      \_____/
      / | | \
     ( /| |\ )
      / | | \
     (  | |  )
""",
        mask=r"""
       MMMMM
      MMMMMMM
     MWMMMMWM
      MMMMMMM
      MMMMMMM
     MMMMMMMM
      MMMMMMM
     MMMMMMMM
""",
    ),
    left=SpriteArt(
        art=r"""
       _____
      /     \
     ( O   O )
      \_____/
      / | | \
     ( /| |\ )
      / | | \
     (  | |  )
""",
        mask=r"""
       MMMMM
      MMMMMMM
     MWMMMMWM
      MMMMMMM
      MMMMMMM
     MMMMMMMM
      MMMMMMM
     MMMMMMMM
""",
    ),
)


# Ghost whale: a paler whale silhouette that drifts slowly across the upper band.
GHOST_WHALE = DirectionalSprite(
    right=SpriteArt(
        art=r"""
        .-----:::
      .'         `.
,---/   .   (o)    \
\__/                \__
""",
        mask=r"""
        WWWWWWWWW
      WW         WW
WWWWWW   W   W      WW
WWWW                WWWW
""",
    ),
    left=SpriteArt(
        art=r"""
     :::-----.
   .'         `.
  /    (o)   .   \---,
__/                \__/
""",
        mask=r"""
     WWWWWWWWW
   WW         WW
  WW   W   W      WWWWWW
WWWW                WWWW
""",
    ),
)


# Skeletal coelacanth: bone-pale, archaic-looking outline.
SKELETAL_COELACANTH = DirectionalSprite(
    right=SpriteArt(
        art=r"""
    .---._
   /|||||| `-._
  ( | | | | o  )>
   \|||||| _.-'
    `---'
""",
        mask=r"""
    WWWWWWW
   WWWWWWWWWWWW
  WWWWWWWWWWWkWW
   WWWWWWWWWWWW
    WWWWW
""",
    ),
    left=SpriteArt(
        art=r"""
        _.---.
    _.-' ||||||\
   <(  o | | | | )
    `-._ ||||||/
         `---'
""",
        mask=r"""
        WWWWWWW
    WWWWWWWWWWWW
   WWkWWWWWWWWWWW
    WWWWWWWWWWWW
         WWWWW
""",
    ),
)


# Deep-sea angel: a translucent angelfish silhouette with a lantern.
DEEP_SEA_ANGEL = DirectionalSprite(
    right=SpriteArt(
        art=r"""
       __
   ___/  \___
  /     o    \*
  \____  ____/
       \/
""",
        mask=r"""
       CC
   CCCCCCCCCC
  CCCCCYCCCCCY
  CCCCCCCCCCCC
       CC
""",
    ),
    left=SpriteArt(
        art=r"""
        __
    ___/  \___
 *  /    o    \
   \____  ____/
        \/
""",
        mask=r"""
        CC
    CCCCCCCCCC
 Y  CCCCYCCCCC
   CCCCCCCCCCCC
        CC
""",
    ),
)


# Submarine wreck: a long-dead silhouette that drifts very slowly.
SUBMARINE_WRECK = DirectionalSprite(
    right=SpriteArt(
        art=r"""
        ___
       |   |__________
   ____|              \
  /  o   o   o   o   o |
  \____________________/
""",
        mask=r"""
        kkk
       kkkkkkkkkkkkkkk
   kkkkkkkkkkkkkkkkkkkkk
  kkRkkkRkkkRkkkRkkkRkkk
  kkkkkkkkkkkkkkkkkkkkk
""",
    ),
    left=SpriteArt(
        art=r"""
              ___
   __________|   |
  /              |____
  | o   o   o   o   o  \
  \____________________/
""",
        mask=r"""
              kkk
       kkkkkkkkkkkkkkk
   kkkkkkkkkkkkkkkkkkkkk
  kkRkkkRkkkRkkkRkkkRkkk
  kkkkkkkkkkkkkkkkkkkkk
""",
    ),
)


# "The thing below": a giant unsettling silhouette that surfaces from the abyss.
THE_THING_BELOW = DirectionalSprite(
    right=SpriteArt(
        art=r"""
  __        __        __
 (  )      (  )      (  )
  \/        \/        \/
   \________||________/
    \  ______||______ /
     \/              \/
""",
        mask=r"""
  kk        kk        kk
 Rkk      Rkkkk      Rkk
  kk        kk        kk
   kkkkkkkkkkkkkkkkkkkkkk
    kkkkkkkkkkkkkkkkkkkk
     kkkkkkkkkkkkkkkkkk
""",
    ),
    left=SpriteArt(
        art=r"""
  __        __        __
 (  )      (  )      (  )
  \/        \/        \/
   \________||________/
    \  ______||______ /
     \/              \/
""",
        mask=r"""
  kk        kk        kk
 Rkk      Rkkkk      Rkk
  kk        kk        kk
   kkkkkkkkkkkkkkkkkkkkkk
    kkkkkkkkkkkkkkkkkkkk
     kkkkkkkkkkkkkkkkkk
""",
    ),
)


# Black koi: the night-time, unsettling cousin of the regular koi pool.
BLACK_KOI = DirectionalSprite(
    right=SpriteArt(
        art=r"""
   ___
  /. o\___
 ( o O o )>
  \___,_/
""",
        mask=r"""
   kkk
  kkkkkkkk
 kkkRkkkkk
  kkkkkkk
""",
    ),
    left=SpriteArt(
        art=r"""
     ___
  ___/o .\
 <( o O o )
   \_,___/
""",
        mask=r"""
     kkk
  kkkkkkkk
 kkkkkRkkk
   kkkkkkk
""",
    ),
)


# The Sleeper: the one-in-666-launches creature. Massive, silent.
THE_SLEEPER = DirectionalSprite(
    right=SpriteArt(
        art=r"""
            .-------------------.
         .-'                     `-.
       /        ___       ___      \
      |        (   )     (   )      |
       \        `-'       `-'      /
        `-._                   _.-'
            `-----.____.------'
""",
        mask=r"""
            BBBBBBBBBBBBBBBBBBBBB
         BBBB                     BBB
       BB        WWW       WWW      BB
      BB        Wkk W     W kkW      BB
       BB        WWW       WWW      BB
        BBBB                   BBBB
            BBBBBBBBBBBBBBBBBBBB
""",
    ),
    left=SpriteArt(
        art=r"""
            .-------------------.
         .-'                     `-.
       /        ___       ___      \
      |        (   )     (   )      |
       \        `-'       `-'      /
        `-._                   _.-'
            `-----.____.------'
""",
        mask=r"""
            BBBBBBBBBBBBBBBBBBBBB
         BBBB                     BBB
       BB        WWW       WWW      BB
      BB        Wkk W     W kkW      BB
       BB        WWW       WWW      BB
        BBBB                   BBBB
            BBBBBBBBBBBBBBBBBBBB
""",
    ),
)
