# Galaxium Lite

<!-- demo-note -->
> **Try it in your browser:** [https://yeokimsiang.github.io/bobathon-galaxium-after/](https://yeokimsiang.github.io/bobathon-galaxium-after/) runs this repo's app after IBM Bob added a refund preview in our lab run on 21 October 2026 ([Bob's commit](https://github.com/yeokimsiang/bobathon-galaxium-after/commit/19486bfa370fdb28675f77677906a09f442cdc17)). Compare with [the starting app](https://yeokimsiang.github.io/bobathon-galaxium-before/). The lab itself: [bobathon-galaxium-lite](https://github.com/yeokimsiang/bobathon-galaxium-lite).
<!-- /demo-note -->

A small interplanetary flight booking API, used for the IBM Bob hands-on lab.
It is a cut-down cousin of IBM's Galaxium Travels demo: FastAPI, plain
`sqlite3` (no ORM), pydantic models and a pytest suite. The same API is also
exposed as **MCP tools** at `/mcp`, so Bob can call it directly.

Based on IBM's [Galaxium Travels](https://github.com/IBM/galaxium-travels) demo, used under the Apache License 2.0 (see `LICENSE`). Cut down and rewritten for the Ingram Bobathon lab.

> **Doing the Bob lab?** Follow the step-by-step guide:
> **<https://yeokimsiang.github.io/bobathon-galaxium-lite/>** (also `GUIDE.md`, next to this folder in the
> download). The guide sits outside this folder on purpose: Bob reads every file in the folder you open, and it
> should work out this project from the code, not from a walkthrough.

## Run it

Requires Python 3.11+ (tested on 3.13).

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS:    source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- MCP endpoint (streamable HTTP): http://localhost:8000/mcp

On first start the app creates `galaxium.db` and seeds demo data. Departure
times are relative to **when the data was seeded**, so if you come back to it
later, stop the server, delete `galaxium.db` and start again.

## Run the tests

```bash
pytest -q
```

Tests use a temporary database and a fixed clock, so they never touch
`galaxium.db` and give the same result whatever the time.

## Endpoints

Each route has an explicit `operation_id`, which is also its MCP tool name.

| Method | Path | operation_id | What it does |
|---|---|---|---|
| GET | `/flights` | `list_flights` | All flights, soonest departure first |
| GET | `/flights/{flight_id}` | `get_flight` | One flight |
| POST | `/bookings` | `book_flight` | Book a flight: `{"user_id": 1, "flight_id": 5}` |
| GET | `/users/{user_id}/bookings` | `list_user_bookings` | A user's bookings |
| POST | `/bookings/{booking_id}/cancel` | `cancel_booking` | Cancel a booking |

Errors return `{"detail": "..."}` with 404 (not found) or 409 (not allowed in
the current state, e.g. already cancelled).

## Seed data

| Booking | User | Flight | Departs | Status |
|---|---|---|---|---|
| 1 | 1 Sally Ride | 1 Earth to Mars (1200) | in ~10 days | booked |
| 2 | 1 Sally Ride | 2 Earth to Moon (300) | in ~3 days | booked |
| 3 | 2 Yuri Gagarin | 3 Mars to Europa (2500) | in ~12 hours | booked |
| 4 | 3 Valentina Tereshkova | 4 Moon to Earth (280) | in ~5 days | cancelled |

Flights 5 (Earth to Titan) and 6 (Venus to Earth) have no bookings.

## Layout

```
app/
  main.py              routes, error handlers, MCP mount (keep the mount last)
  db.py                schema, connection, seed data, ISO-8601 time helpers
  schemas.py           pydantic request/response models
  services/            business logic; raise NotFoundError / ConflictError
    flights.py  bookings.py  users.py
tests/                 pytest; conftest.py gives a temp DB and a fixed clock
plans/                 put implementation plans here
fallback/              a ready-made plan if you fall behind in the lab
docs/STRETCH.md        stretch goal
.bob/                  Bob configuration (see below)
```

Conventions: services take a `sqlite3.Connection` and return plain dicts;
anything time-dependent takes an explicit `now` (routes get it from the
`get_now` dependency, tests override it). Times are stored as ISO-8601 UTC
strings like `2030-01-01T12:00:00Z`.

## Bob configuration (`.bob/`)

`.bob/` holds this project's own Bob settings. It's committed with the code, so everyone who opens the project gets
the same Bob set-up. The kit is ours, not built into Bob: three small files, each showing one Bob feature.

| File | Bob feature | What it gives Bob |
|---|---|---|
| [`mcp.json`](.bob/mcp.json) | MCP server | Tools that call this app's own API |
| [`custom_modes.yaml`](.bob/custom_modes.yaml) | Custom mode | A **Reviewer** mode that can read code but not change it |
| [`skills/verify/SKILL.md`](.bob/skills/verify/SKILL.md) | Skill | One fixed way to run the tests and report the result |

**How Bob finds it.** Bob reads `.bob/` from the root of the folder you open. Open *this* folder (File > Open
Folder), not a folder above it, and choose *Yes, I trust the authors* when Bob asks. Your own Bob settings live in
`~/.bob/settings/` (`mcp.json`, `custom_modes.yaml`) and `~/.bob/skills/`. Where both define the same thing, the
project's version wins.

The pictures below show each file next to what it made Bob do. They are a recreated IDE around real output from
Bob Shell 2.0.6 runs of this project (20–21 Oct 2026). Your Bob's wording will differ.

### `mcp.json`: connect Bob to this app's API

```json
{
  "mcpServers": {
    "galaxium-lite": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

| Line | What it says | Why it's there |
|---|---|---|
| 3 | `"galaxium-lite"` | The server's name. Bob shows each tool as `galaxium-lite › <tool>`, and you can name the server in a prompt ("use the galaxium-lite MCP tool to …"). |
| 4 | `"type": "streamable-http"` | The app serves MCP over plain HTTP: `mcp.mount_http()` in [`app/main.py`](app/main.py) (line 122). Nothing extra to install or launch. |
| 5 | `"url": "http://localhost:8000/mcp"` | Where the app listens. **The app must be running** (`uvicorn app.main:app --port 8000`); Bob doesn't start it. Change the port here if you run the app on another one. |

**Why we built it this way.** The app turns its own routes into MCP tools: `FastApiMCP(app, …)` in
[`app/main.py`](app/main.py) (line 121) reads every route that exists when it's created, and each route's
`operation_id` becomes the tool's name (line 54). So Bob can check behaviour through the real running API instead
of only reading the code. Two consequences you'll see in the code:

- `FastApiMCP` must stay the **last** thing in `main.py` (the comment on lines 119–120). A route added below it
  doesn't become a tool.
- Every route has an explicit `operation_id`, so tool names stay short and stable (`list_flights`, `cancel_booking`).

**What's left out on purpose.** No `headers`: the app runs on your machine without authentication, and Bob's docs
say never to put tokens in this file. No `alwaysAllow`: Bob asks you before every tool call.

**In Bob IDE:** the server shows under Bob's settings menu > **MCP**. If you start the app after Bob, press
**Restart** there.

![Bob calling a tool on the galaxium-lite MCP server, with .bob/mcp.json open: line 3 names the server, line 5 is its URL](https://yeokimsiang.github.io/bobathon-galaxium-lite/media/kit-mcp.png)

### `custom_modes.yaml`: a Reviewer that can't edit

```yaml
customModes:
  - slug: reviewer
    name: Reviewer
    description: Read-only code reviewer. Comments on code; never edits it.
    roleDefinition: >-
      You are a strict, read-only code reviewer for the Galaxium Lite flight
      booking API (FastAPI + sqlite3). You read code and give clear, actionable
      feedback: correctness bugs, missing or weak tests, edge cases (time zones,
      boundaries, already-cancelled bookings), naming, structure, and
      consistency with the existing style. You never create, edit or delete files.
    whenToUse: Use when you want a review of a change or a file without any edits being made.
    customInstructions: >-
      Start with a one-paragraph summary, then list findings as
      "file:line - issue - suggested fix". Mark each finding BLOCKING (must fix
      before merge) or SUGGESTION (nice to have). Be direct; do not pad the
      review with praise. If something cannot be judged without running it,
      say so instead of guessing.
    groups:
      - read
```

| Lines | What it says | Why it's there |
|---|---|---|
| 2 | `slug: reviewer` | The mode's id. It also becomes a slash command: `/reviewer`. |
| 3–4 | `name`, `description` | What you see in the mode picker, next to Agent, Plan and Ask. |
| 5–10 | `roleDefinition` | Who Bob is in this mode. It names this app's stack and the edge cases worth checking here: time zones, boundaries, cancelled bookings. A generic "review this code" finds generic issues. |
| 11 | `whenToUse` | Tells Bob when this mode fits, if it is choosing a mode for a task. |
| 12–17 | `customInstructions` | The shape of the answer: a summary, then `file:line - issue - suggested fix`, each marked BLOCKING or SUGGESTION. A fixed shape makes reviews easy to compare and act on. |
| 18–19 | `groups: [read]` | **The line that matters.** Tool groups decide what a mode can *do*. With only `read`, Bob can open and search files but has no tools to edit them, run commands, call MCP or load skills. |

**Why we built it this way.** Line 10 *asks* Bob never to edit; line 19 makes sure it can't. Instructions are a
request, tool groups are a limit. That's the difference to keep in mind when you write your own modes.

![Bob in Reviewer mode beside .bob/custom_modes.yaml: it read six files, changed none, and opened its review with a summary and findings by file and line](https://yeokimsiang.github.io/bobathon-galaxium-lite/media/kit-reviewer.png)

**Reviewer or `/review`?** Both review code. Reviewer is our mode: a chat answer, shaped by the instructions above,
in Bob IDE and Bob Shell. `/review` is built into Bob IDE: it reviews your uncommitted changes (or a branch) and
lists findings in the **Bob Findings** panel, each with **Fix with Bob** or **Dismiss**.

### `skills/verify/SKILL.md`: one way to check the work

````markdown
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
````

| Lines | What it says | Why it's there |
|---|---|---|
| 2 | `name: verify` | The skill's name, shown when Bob loads it ("Loaded skill verify"). |
| 3 | `description: … Use after every implementation, and whenever the user asks to … run tests …` | **The line that matters.** Bob reads the description to decide when to load a skill; a skill without one is ignored. This one names the moments, so Bob loads it without being asked. In our recorded runs Bob loaded it on its own in all three runs that ran the tests. |
| 8 | "Run the tests yourself. Do not just describe what to run." | Bob should prove it, not suggest it. |
| 18–20 | Use the `.venv` interpreter; on Windows fall back to `py` | The two things that actually go wrong on a fresh Windows machine: the wrong Python, and the Microsoft Store `python` alias. |
| 29–31 | The `Suite / Result / Detail` table | Every test report comes back in the same shape, so you can read it at a glance. |
| 38 | "Never report a pass you did not see in the output." | Guards against a confident "all tests pass" that nobody ran. |

**Why we built it this way.** "Run the tests" is something you'd otherwise retype in every prompt, with slightly
different words each time. A skill writes it down once, and the description decides when it applies. In Bob IDE,
Bob asks your permission before it loads a skill, unless you auto-approve skills.

![Bob loading the verify skill without being asked, with SKILL.md open: line 3 says when to use it, lines 29–31 are the report Bob gives](https://yeokimsiang.github.io/bobathon-galaxium-lite/media/kit-verify.png)

### What's not in `.bob/`, on purpose

| Missing | Why |
|---|---|
| `AGENTS.md` | Bob's `/init` writes it: a root `AGENTS.md`, plus one per mode under `.bob/rules-<mode>/`. Starting without one lets you see what Bob works out from the code alone. They're plain files: read them, edit them, commit them. |
| Hooks (`.bob/settings.json`) | An earlier version of this kit had a hook that ran the tests before every commit. We took it out to keep the lab short. |
| `.bobignore` | Nothing in this project needs hiding from Bob. |
| Auto-approval | Nothing is pre-approved, so Bob asks before every edit, command, tool call and skill. You can loosen that in Bob's settings once you trust a workflow. |

## Credits and copyright

- **The app** (`app/`, `tests/`) is based on IBM's [Galaxium Travels](https://github.com/IBM/galaxium-travels) demo, used under the Apache License 2.0
  (see `LICENSE`), and cut down and rewritten for this lab. Each of those files says so at its end.
- **The lab's exercise**, a refund preview on cancel, follows a scenario from IBM's Galaxium Travels demos, with simpler
  refund rules of our own.
- **In the `.bob/` kit**, the Reviewer mode (`custom_modes.yaml`) and the verify skill (`skills/verify/SKILL.md`) are
  adapted from the `.bob/` configuration in IBM's Galaxium Travels, under the same licence. Each says so at its end.
- **The lab guide and the before/after demo pages**: © 2026 Ingram Micro. All rights reserved.
- **The guide's videos and screenshots** are recordings of IBM Bob. IBM, IBM Bob and the IBM logo are trademarks of
  International Business Machines Corporation.
