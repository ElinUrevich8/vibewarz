"""Trivial example bot: always go STRAIGHT.

Run:
    vibewarz play sdk-python/src/vibewarz/examples/straight_curve.py --mode practice
"""

from vibewarz import Bot, run


class StraightBot(Bot):
    game = "curve"

    def act(self, state):
        return {"turn": "STRAIGHT"}


if __name__ == "__main__":
    run(StraightBot(), mode="practice")
