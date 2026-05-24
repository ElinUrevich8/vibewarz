# vibewarz — Python SDK

```bash
pip install vibewarz
```

Write a bot:

```python
from vibewarz import Bot, run

class MyBot(Bot):
    game = "curve"
    def act(self, state):
        return {"turn": "STRAIGHT"}

run(MyBot(), mode="practice")
```

Or use the CLI:

```bash
vibewarz login
vibewarz play my_bot.py --mode ranked --loop 50
```
