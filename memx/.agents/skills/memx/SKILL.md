---
name: memx
description: memx best practices and conventions. Use when working with memx. Keeps memx code clean and up to date with the latest features and patterns.
---

# memx

Official memx skill to write code with best practices, keeping up to date with new versions and patterns.

## Quick Reference

* Two layers: `Engine` (factory, one per backend/process) and `Memory` (session, one per conversation).
* Create a new session: `engine.create_session()`. Resume one: `await engine.get_session(id)`; returns `None` if not found.
* All methods are `async`; blocking variants live under `.sync`. Never call `.sync` methods inside `async` code.
* Messages are `list[JSON]`: orjson-serializable dicts (`{"role": ..., "content": ...}`). No forced schema.
* Session IDs are UUIDv7, auto-assigned; get them with `m.get_id()` and persist to resume later.
* Blocking startup work (`setup=True`, `ttl=...`) runs at engine init (call it once at app startup, not per request).
* Close with `await engine.close()` (blocking: `engine.sync.close()`). Same call for every engine.
* Extra kwargs on `RedisEngine` are forwarded to both redis clients.

## General guidelines

Create one engine per backend and reuse it across sessions; engines hold the connection pools/clients and session makers.

```python
from memx.engine.sqlite import SQLiteEngine

engine = SQLiteEngine("sqlite+aiosqlite:///memx.db", "memx-messages", setup=True)

m1 = engine.create_session()  # new session, UUIDv7 auto-assigned
await m1.add([{"role": "user", "content": "Hello"}])
messages = await m1.get()

session_id = m1.get_id()

# later, maybe in another process/request:
m2 = await engine.get_session(session_id)
if m2 is not None:
    await m2.add([{"role": "agent", "content": "Hi!"}])
```

* Prefer the async API (`await m.add(...)`, `await m.get(...)`). Use `m.sync.add(...)` / `m.sync.get(...)` only from blocking code (scripts, sync frameworks, threadpools).
* `get()` returns the full history; `get_one()` returns the last message; `put(data)` is shorthand for `add([data])`.
* Memories are cheap to create and share the engine's connections - don't cache `AsyncSession`/clients yourself.
* Keep messages plain JSON dicts. If your framework returns its own message types, convert to `list[dict]` before `add()`.

## SQLiteEngine

Use the `sqlite+aiosqlite` driver; the engine derives its sync counterpart from the same URI.

```python
from memx.engine.sqlite import SQLiteEngine

engine = SQLiteEngine(
    "sqlite+aiosqlite:///message_store.db",  # aiosqlite driver required
    "memx-messages",
    setup=True,  # creates table + index (blocking) once at startup
)
```

* `setup=True` runs the `CREATE TABLE IF NOT EXISTS` + index script synchronously at init. Keep it out of request paths.
* Avoid `sqlite+aiosqlite:///:memory:` when resuming sessions or mixing `.sync` and async paths: each connection gets its own in-memory DB. Use a file URI instead.
* Close with `await engine.close()`.

## PostgresEngine

Use the `postgresql+psycopg` driver, it is enforced. Any other driver raises `ValueError`.

```python
from memx.engine.postgres import PostgresEngine

engine = PostgresEngine(
    "postgresql+psycopg://admin:1234@localhost:5433/test-database",
    "memx-messages",
    schema="public",  # sets search_path
    setup=True,  # creates the table (blocking) - once at startup
)

m1 = engine.create_session()
await m1.add([{"role": "user", "content": "Hello"}])

m2 = await engine.get_session(m1.get_id())
await engine.close()
```

* Session lookup uses the table's primary key - expect O(1) resumes.
* Close with `await engine.close()`.

## MongoDBEngine

One document per session, updated with `$push` upserts. No `setup` flag; passing `ttl` creates the TTL index.

```python
from memx.engine.mongodb import MongoDBEngine

engine = MongoDBEngine(
    "mongodb://admin:1234@localhost:27017",
    "memx-test",
    "memx-messages",
    ttl=3600,  # seconds; creates a TTL index on created_at (blocking) - omit or None to skip
)

m1 = engine.create_session()
await m1.add([{"role": "user", "content": "Hello"}])

m2 = await engine.get_session(m1.get_id())
await engine.close()
```

* `ttl` sets expiration in seconds.
* Close with `await engine.close()`.

## RedisEngine

Requires RedisJSON - built into Redis ≥ 8; older servers need the RedisJSON module. `setup=True` verifies both the connection and JSON support.

```python
from memx.engine.redis import RedisEngine

engine = RedisEngine(
    "redis://default:1234@localhost:6379/0",
    setup=True,  # pings + checks RedisJSON (blocking) - once at startup
    ttl=3600,  # per-key TTL in seconds
    max_connections=10,  # extra kwargs are forwarded to both sync and async clients
)

m1 = engine.create_session()
await m1.add([{"role": "user", "content": "Hello"}])

m2 = await engine.get_session(m1.get_id())
await engine.close()
```

* `ttl` is applied with `EXPIRE` when the key is first created.
* Missing key `await engine.get_session(id)` returns `None`; `create_session()` always succeeds.
* Close with `await engine.close()`.
