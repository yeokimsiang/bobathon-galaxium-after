---
name: verify
description: Run the Galaxium Lite test suite and summarise pass/fail. Use after every implementation, and whenever the user asks to verify, validate, run tests or confirm a change works.
---

# Verify

Run the tests yourself. Do not just describe what to run.

## Step 1 - Run pytest

From the repository root:

```bash
python -m pytest -q
```

If a `.venv` exists, use its interpreter (`.venv/Scripts/python` on Windows,
`.venv/bin/python` on macOS/Linux). On Windows, if `python` opens the Microsoft
Store or is not found, use `py -m pytest -q` instead.

If pytest is missing, install the dependencies first: `pip install -r requirements.txt`.

## Step 2 - Summarise

Report in this shape:

```
Suite   | Result | Detail
--------|--------|---------------------------
pytest  | PASS   | <final pytest line, e.g. "11 passed in 0.3s">
```

- Use PASS or FAIL. Quote the final pytest summary line exactly.
- If anything failed: list each failing test by node id
  (e.g. `tests/test_bookings.py::test_cancel_booking`), show the assertion
  message, and suggest the most likely fix.
- Never report a pass you did not see in the output.

Adapted from the verify skill in IBM's Galaxium Travels (.bob/skills/verify/SKILL.md, https://github.com/IBM/galaxium-travels), Apache License 2.0; changed for Galaxium Lite.
