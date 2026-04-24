"""Unauthenticated Reddit JSON API client.

Uses the public JSON endpoints (no OAuth required).
Throttled to 1 request/second per Reddit's rate-limit guidance.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from src.constants import (
    REDDIT_BASE_URL,
    REDDIT_MAX_BODY_CHARS,
    REDDIT_MAX_COMMENT_CHARS,
    REDDIT_MAX_COMMENTS,
    REDDIT_MAX_THREADS,
    REDDIT_USER_AGENT,
)
from src.schemas.reddit import Comment, Thread


class RedditClient:
    """Read-only client for the Reddit JSON API."""

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        self._last_request_at: float = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_request_at = time.monotonic()

    def _get(self, path: str, **params: Any) -> Any:
        self._throttle()
        response = self._session.get(f"{REDDIT_BASE_URL}{path}", params=params)
        response.raise_for_status()
        return response.json()

    def get_hot_threads(self, subreddit: str, *, limit: int = REDDIT_MAX_THREADS) -> list[Thread]:
        """Return the top `limit` hot threads from `subreddit`, without comments."""
        data = self._get(f"/r/{subreddit}/hot.json", limit=limit)
        return [
            self._parse_post(child["data"])
            for child in data["data"]["children"]
            if child["kind"] == "t3"
        ]

    def get_thread_comments(
        self, subreddit: str, post_id: str, *, limit: int = REDDIT_MAX_COMMENTS
    ) -> Thread:
        """Return a thread with its top `limit` comments (up to 1 level of replies)."""
        data = self._get(
            f"/r/{subreddit}/comments/{post_id}.json",
            limit=limit,
            depth=2,
        )
        thread = self._parse_post(data[0]["data"]["children"][0]["data"])
        raw_comments = [
            self._parse_comment(child["data"])
            for child in data[1]["data"]["children"]
            if child["kind"] == "t1"
        ]
        filtered = [
            c for c in raw_comments
            if c.score > 0 and c.body not in {"[removed]", "[deleted]"}
        ]
        return thread.model_copy(update={"top_comments": filtered[:limit]})

    def _parse_post(self, data: dict[str, Any]) -> Thread:
        body = data.get("selftext", "") or ""
        if body in {"[removed]", "[deleted]"}:
            body = ""
        return Thread(
            id=data["id"],
            title=data.get("title", ""),
            body=body[:REDDIT_MAX_BODY_CHARS],
            url=data.get("url", ""),
            score=data.get("score", 0),
            num_comments=data.get("num_comments", 0),
            subreddit=data.get("subreddit", ""),
            top_comments=[],
        )

    def _parse_comment(self, data: dict[str, Any]) -> Comment:
        body = data.get("body", "")
        if len(body) > REDDIT_MAX_COMMENT_CHARS:
            body = body[:REDDIT_MAX_COMMENT_CHARS] + "..."
        replies: list[Comment] = []
        replies_data = data.get("replies", "")
        if isinstance(replies_data, dict):
            for child in replies_data.get("data", {}).get("children", []):
                if child.get("kind") != "t1":
                    continue
                rd = child["data"]
                rb = rd.get("body", "")
                if rb in {"[removed]", "[deleted]"} or rd.get("score", 0) <= 0:
                    continue
                if len(rb) > REDDIT_MAX_COMMENT_CHARS:
                    rb = rb[:REDDIT_MAX_COMMENT_CHARS] + "..."
                replies.append(Comment(body=rb, score=rd.get("score", 0)))
        return Comment(body=body, score=data.get("score", 0), replies=replies)


def make_reddit_client() -> RedditClient:
    """Build a RedditClient with the project User-Agent header."""
    session = requests.Session()
    session.headers.update({"User-Agent": REDDIT_USER_AGENT})
    return RedditClient(session)
