# Types and boundaries

## Parse, don't validate

Validate external input once at the boundary and return typed domain values:

```python
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NewType

UserId = NewType("UserId", str)

@dataclass(frozen=True)
class UserRequest:
    user_id: UserId

def parse_user_request(data: object) -> UserRequest:
    if not isinstance(data, Mapping):
        raise TypeError("Expected a user request mapping")
    user_id = data.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("user_id must be a nonempty string")
    return UserRequest(user_id=UserId(user_id))
```

Route untrusted HTTP, SDK, and DB values through parsers. `NewType` and frozen
dataclasses do not validate input; freezing only prevents ordinary reassignment.
If every construction must enforce invariants, use `__post_init__` or a validating
model. Pydantic validators enforce values, but a `str` field remains `str` to the
type checker. Add a semantic type when static distinction matters.

## Semantic types for domain concepts

Use `NewType` when confusing two primitive values would be a domain error, such as
passing `OrgId` where `UserId` is required. It preserves the runtime value while
adding a distinct static type; `TypeAlias` only supplies another name.

Apply this to meaningful IDs, amounts, slugs, tokens, emails, URLs, and paths.
Leave generic counters and buffer sizes as primitives.
