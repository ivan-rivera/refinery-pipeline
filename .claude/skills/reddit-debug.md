---
name: reddit-debug
description: Read-only debugging access to the Reddit JSON API via RedditClient. Use to inspect hot threads, post comments, and LLM-ready text output without running the full pipeline. No authentication or API key required.
---

# Reddit Debug Access

Inspect Reddit data using the project's `RedditClient`. All calls are read-only and unauthenticated. The client enforces a 1 req/s throttle automatically — multi-step snippets will take a few seconds.

Run all commands from the worktree root with `uv run python -c "..."`.

---

## List hot threads from a subreddit

Replace `wallstreetsilver` with any subreddit. Adjust `limit` (default 10).

```bash
uv run python -c "
from src.integrations.reddit import make_reddit_client

client = make_reddit_client()
threads = client.get_hot_threads('wallstreetsilver', limit=5)

for t in threads:
    print(f'[{t.score:>5}] {t.id}  {t.title[:80]}')
"
```

---

## Fetch a thread with comments and print the LLM text

This is the primary output consumed by LLM agents — use it to verify the text looks sensible before wiring it into a prompt.

```bash
uv run python -c "
from src.integrations.reddit import make_reddit_client

client = make_reddit_client()
threads = client.get_hot_threads('goldsilver', limit=3)
if not threads:
    print('No threads returned')
else:
    thread = client.get_thread_comments('goldsilver', threads[0].id, limit=10)
    print(thread.to_text())
"
```

---

## Inspect raw comment structure

Use when debugging comment parsing — shows body, score, and reply count per comment.

```bash
uv run python -c "
from src.integrations.reddit import make_reddit_client

client = make_reddit_client()
threads = client.get_hot_threads('goldsilver', limit=1)
thread = client.get_thread_comments('goldsilver', threads[0].id, limit=5)

print(f'Thread: {thread.title}')
print(f'Comments fetched: {len(thread.top_comments)}')
for i, c in enumerate(thread.top_comments, 1):
    print(f'  [{i}] score={c.score} replies={len(c.replies)} body={c.body[:60]!r}')
    for r in c.replies:
        print(f'       reply score={r.score} body={r.body[:50]!r}')
"
```

---

## Check all precious metals subreddits

Verifies connectivity and returns the top thread title from each configured subreddit.

```bash
uv run python -c "
from src.constants import PRECIOUS_METALS_SUBREDDITS
from src.integrations.reddit import make_reddit_client

client = make_reddit_client()
for sub in PRECIOUS_METALS_SUBREDDITS:
    threads = client.get_hot_threads(sub, limit=1)
    if threads:
        print(f'r/{sub}: [{threads[0].score}] {threads[0].title[:70]}')
    else:
        print(f'r/{sub}: NO THREADS RETURNED')
"
```

---

## Fetch a specific post by ID

Use when you already have a post ID (e.g. from a prior listing call).

```bash
uv run python -c "
from src.integrations.reddit import make_reddit_client

POST_ID = 'abc123'        # replace with real post ID
SUBREDDIT = 'goldsilver'  # replace with subreddit

client = make_reddit_client()
thread = client.get_thread_comments(SUBREDDIT, POST_ID, limit=10)
print(thread.to_text())
"
```

---

## Notes

- **No API key or `.env` loading required** — the Reddit JSON API is public
- **Throttle:** 1 request/second enforced automatically; fetching N threads takes at least N+1 seconds
- **Filtering:** comments with `score <= 0` or body `[removed]`/`[deleted]` are silently dropped
- **Truncation:** post bodies capped at 500 chars, comment bodies at 300 chars with `...`
- **Depth:** replies are fetched 1 level deep only — no deep nesting
- **Search:** not implemented in `RedditClient` — use the subreddit listing with `limit` to browse instead
