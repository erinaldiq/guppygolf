import sys

import pyglet
from config import ROUND
from game.loop import Loop
from render.window import GolfWindow


def main():





    sys.setswitchinterval(0.0005)
    cfg = ROUND[0]
    loop = Loop(cfg, courses=ROUND)
    win = GolfWindow(cfg, loop)
    pyglet.app.run()


if __name__ == "__main__":
    main()
