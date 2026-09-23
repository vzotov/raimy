# Local Verification Guide

How to actually exercise a feature on localhost before claiming it works. Every command here has been run and verified.

**Prefer this over reasoning about behavior.** Agent output depends on live LLM calls — static reading cannot tell you what a prompt change actually produces.

---

## 1. Bring up the stack

Backend runs in Docker; the frontend runs on the host.

```bash
# from repo root
docker compose up -d postgres redis auth-service raimy-api agent-service

# frontend (separate terminal, host — not Docker)
cd client && bun dev          # http://localhost:3010
```

`server/` is volume-mounted into both Python containers, so **code changes need only a restart, never a rebuild**:

```bash
docker compose restart raimy-api agent-service
```

Migrations run automatically on `raimy-api` startup (`AUTO_MIGRATE=true`).

### Health check

```bash
curl -s localhost:3010 -o /dev/null -w "frontend %{http_code}\n"
curl -s localhost:8000/health   # API      — also shows websocket_connections
curl -s localhost:8003/health   # agent-service
docker compose ps --format "table {{.Service}}\t{{.Status}}"
```

| Service | Port |
|---|---|
| frontend (Next dev) | 3010 |
| raimy-api | 8000 |
| auth-service | 8001 |
| agent-service | 8003 |

---

## 2. Local test account

```
email:    raimy.test@example.com
password: RaimyTest12345!
```

Local-only throwaway on a localhost database. Not a real credential — never reuse this password anywhere else.

If the account is missing (fresh DB, wiped volume), recreate it. **Signup emails do not send locally** — `RESEND_API_KEY` is unset — so pull the verification token straight out of Redis:

```bash
EMAIL="raimy.test@example.com"; PASS="RaimyTest12345!"

curl -s -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"name\":\"Raimy Test\"}"

TOKEN=$(docker compose exec -T redis redis-cli --raw GET "email_verify_pending:$EMAIL" | tr -d '\r\n')
curl -s -o /dev/null -w "verify %{http_code}\n" "http://localhost:8001/auth/verify-email?token=$TOKEN"

# confirm
curl -s -o /dev/null -w "login %{http_code}\n" -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}"
```

Both should return `200`.

---

## 3. Browser verification (chrome-devtools MCP)

Use this for anything user-visible: rendering, layout, button labels, streamed UI updates.

```
mcp__chrome-devtools__new_page       url: http://localhost:3010
mcp__chrome-devtools__take_snapshot  # a11y tree + uids — prefer over screenshots
mcp__chrome-devtools__fill           # email, then password
mcp__chrome-devtools__click          # "Sign in"
mcp__chrome-devtools__wait_for       text: ["<expected UI text>"]
```

**Sign in with the email/password form — never "Sign in with Google".** Google blocks OAuth from a
DevTools-controlled browser with *"This browser or app may not be secure."* The password form is unaffected.

Notes:
- `take_snapshot` beats `take_screenshot` for assertions: it returns text content you can grep. Screenshot only when layout/visual styling is the thing under test.
- `wait_for` on expected text is the reliable way to await a streamed agent response (recipes take ~40s).
- Check `list_console_messages` with `types: ["error","warn"]` before declaring success.
- Known benign dev noise: a WebSocket "closed before connection established" warning on first mount. That's React StrictMode double-mounting; it reconnects immediately. Not a real failure.
- A fresh `new_page` may be signed out even if another tab is authenticated.

---

## 4. Fast agent checks (no browser)

For backend/prompt behavior, skip the UI — it's far faster and gives raw structured output.
Write a script, copy it in, run it inside the container (dependencies live there, not on the host):

```bash
cat > /tmp/t.py <<'EOF'
import asyncio, sys
sys.path.insert(0, '/app/server/agent-service')
from agents.recipe_creator.agent import RecipeCreatorAgent

async def main():
    agent = RecipeCreatorAgent()
    out = {}
    async for ev in agent.run_streaming(
        message="Margarita",
        message_history=[],
        session_id="t",
        session_data={"recipe": None, "user_language": "English"},
    ):
        if ev.type == "thinking":
            continue
        out.setdefault(ev.type, ev.data)   # first payload per event type
    print(out.get("metadata"), out.get("equipment"))

asyncio.run(main())
EOF
docker compose cp /tmp/t.py agent-service:/tmp/t.py
docker compose exec -T agent-service python /tmp/t.py
```

Useful variations:
- **Modification flows** — pass an existing recipe dict as `session_data["recipe"]` and send e.g. `"I don't have a shaker"`. Check which events re-emit: absence of an event means that field was preserved, not lost.
- **Unified agent paths** — import `agents.unified.agent.UnifiedAgent` and call `_analyze_intent(...)` to check intent classification, or `_handle_step_action(...)` for kitchen-step guidance.
- **Always test both domains.** A cocktail change can silently regress food recipes; run a dish (e.g. "Spaghetti carbonara") as a control.

Each run is a real, billable OpenAI call taking ~40s, and output varies between runs. Assert on
structure (a tag exists, units are plausible, a field is absent) rather than exact strings.

Clean up scripts when done: `docker compose exec -T agent-service rm -f /tmp/t.py`

---

## 5. Database inspection

```bash
docker compose exec -T postgres psql -U raimy_user -d raimy -c "\d recipes"
docker compose exec -T postgres psql -U raimy_user -d raimy -c "SELECT version_num FROM alembic_version;"
```

Python-level checks (services layer, round-trips) run in the **raimy-api** container with `sys.path` at `/app/server`:

```python
import sys; sys.path.insert(0, '/app/server')
from app.services import database_service
```

---

## 6. Clean up

Verification writes real rows to the dev database. Remove them, especially recipes — they show up in a real user's library.

```bash
docker compose exec -T postgres psql -U raimy_user -d raimy -c "
DELETE FROM recipes       WHERE user_id = 'raimy.test@example.com';
DELETE FROM chat_sessions WHERE user_id = 'raimy.test@example.com';
"
```

Keep the test account itself; delete it only on request:

```bash
docker compose exec -T postgres psql -U raimy_user -d raimy -c "
DELETE FROM users WHERE email = 'raimy.test@example.com';"
```

**Never run `docker compose down -v` or any docker prune** — that destroys the postgres volume and all local data.

---

## Gotchas

- **`bun run lint` rewrites the repo.** It is `biome check --write ./src`, and the codebase is not biome-clean — it will reformat dozens of untouched files. For verification use `bunx tsc --noEmit` instead. If you do run it, `git checkout -- client/` and re-apply your own edits.
- **Port 3010 may already be in use** — the frontend is often already running. Check before starting another.
- **Restart Python containers after backend edits.** The volume mount makes files current, but a running process keeps the old code in memory.
- **Prompt placeholders and callers must stay in sync.** Adding `{foo}` to a prompt without passing `foo=` to its `.format()` raises `KeyError` at runtime, not at import. Verify by extracting `re.findall(r'{(\w+)}', PROMPT)` and diffing against the call's kwargs.
