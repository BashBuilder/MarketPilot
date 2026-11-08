"""Minimal SSE frame parser for API tests."""

import json


def parse_sse(text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for block in text.strip().split("\n\n"):
        if not block or block.startswith(":"):
            continue
        fields: dict[str, str] = {}
        for line in block.splitlines():
            name, _, value = line.partition(": ")
            fields[name] = value
        events.append(
            {
                "id": fields["id"],
                "event": fields["event"],
                "data": json.loads(fields["data"]),
            }
        )
    return events
