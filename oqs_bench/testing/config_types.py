from typing import TypedDict, List


class KEMConfig(TypedDict):
    algorithm: str
    runner: str
    variants: List[str]


class SignConfig(KEMConfig):
    ...
