# CircleForge screenshot demo

Use this when you want a simple screenshot showing CircleForge replying in its current CLI form.

## Minimal commands

```bash
python3 main.py version
python3 main.py failsafe-status
python3 main.py communicator-message
```

## Better-looking demo

This seeds one human thread first so the answer is more obviously conversational.

```bash
python3 main.py human-exchange current-speaker "Please keep working on backup confidence and explain why it matters." --response "Understood. I will keep that thread active."
python3 main.py speak
# optional behind-the-curtain inspect:
python3 main.py communicator-message
```

## What the screenshot should communicate

- CircleForge has a continuing communicator
- it remembers a human thread
- it can generate outward language from internal state
- it is not just printing a random canned quote

## Suggested caption

> CircleForge is an early local persistent-being substrate. The communicator answer below is generated from current continuity state, not just a static prompt.
