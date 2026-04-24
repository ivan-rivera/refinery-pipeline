"""Typed models for Reddit JSON API data."""

from __future__ import annotations

from pydantic import BaseModel


class Comment(BaseModel):
    body: str
    score: int
    replies: list[Comment] = []


Comment.model_rebuild()


class Thread(BaseModel):
    id: str
    title: str
    body: str
    url: str
    score: int
    num_comments: int
    subreddit: str
    top_comments: list[Comment]

    def to_text(self) -> str:
        """Render thread as indented plain text for LLM agent context."""
        lines: list[str] = [
            f"r/{self.subreddit} — {self.title!r} (score: {self.score}, {self.num_comments} comments)"
        ]
        if self.body:
            lines += ["", self.body, ""]
        for comment in self.top_comments:
            lines.append(f"[+{comment.score}] {comment.body}")
            for reply in comment.replies:
                lines.append(f"  [+{reply.score}] {reply.body}")
        return "\n".join(lines)
