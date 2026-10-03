"""camelCase <-> snake_case helpers.

The frontend's TypeScript interfaces are camelCase. Internally the backend
stays snake_case (idiomatic Python / DB columns). Pydantic schemas use
`to_camel` as an alias generator so JSON responses match the frontend's
existing `src/types/index.ts` contracts exactly, with no frontend changes
required beyond pointing `service.ts` at real HTTP calls.
"""

from __future__ import annotations


def to_camel(snake: str) -> str:
    first, *rest = snake.split("_")
    return first + "".join(word.capitalize() for word in rest)
