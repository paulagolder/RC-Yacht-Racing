"""boat_class.py - boat classes, such as DF95 or Victoria.

The club's classes are kept in yachtclasses.xml (see storage/boat_class_store.py). Each has:

    key       a short id, such as "df95"
    fullname  the name shown on screen and used in the sailors and competition files: "DF95"
    cypher    a short code for the class: "95"
    symbol    one character that marks the class: "@"

A class name in a sailor or competition is still just text, so any class can be used.
Classes are matched ignoring case and spaces: "DF95", "df95" and "DF 95" are the same class.
"""

from __future__ import annotations

from dataclasses import dataclass


def class_key(boat_class: str) -> str:
    """The form used to compare classes: 'Df 95' -> 'DF95'."""
    return "".join(boat_class.split()).upper()


@dataclass(frozen=True)
class BoatClass:
    key: str
    fullname: str
    cypher: str = ""
    symbol: str = ""

    def problem(self) -> str | None:
        """What is wrong with this class on its own, or None if nothing is."""
        if not (self.key.strip() and self.fullname.strip()):
            return "A boat class needs a key and a full name."
        if len(self.symbol.strip()) > 1:
            return "A boat class symbol must be a single character."
        return None


DEFAULT_BOAT_CLASSES = [
    BoatClass("df65", "DF65", "65", "#"),
    BoatClass("rg65", "RG65", "rg", "$"),
    BoatClass("df95", "DF95", "95", "@"),
    BoatClass("victoria", "Victoria", "Va", "*"),
]

# Suggestions for the class boxes on screen when yachtclasses.xml cannot be read.
BOAT_CLASSES = [c.fullname for c in DEFAULT_BOAT_CLASSES]


class BoatClassList:
    def __init__(self, classes: list[BoatClass] | None = None):
        self.classes: list[BoatClass] = list(classes or [])

    def __len__(self) -> int:
        return len(self.classes)

    def names(self) -> list[str]:
        """The full names, in file order, for the class boxes on screen."""
        return [c.fullname for c in self.classes]

    def find(self, name: str) -> BoatClass | None:
        """The class with this key or full name (ignoring case and spaces), or None."""
        wanted = class_key(name)
        return next((c for c in self.classes
                     if wanted in (class_key(c.key), class_key(c.fullname))), None)

    # -- changing ---------------------------------------------------------------------------

    def check(self, boat_class: BoatClass, ignore: int | None = None) -> str | None:
        """Why this class cannot be added (or replace classes[ignore]), or None if it can."""
        problem = boat_class.problem()
        if problem:
            return problem
        for i, other in enumerate(self.classes):
            if i == ignore:
                continue
            if class_key(other.key) == class_key(boat_class.key):
                return f"{other.fullname} already has the key '{other.key}'."
            if class_key(other.fullname) == class_key(boat_class.fullname):
                return f"There is already a class called {other.fullname}."
            if boat_class.cypher.strip() and class_key(other.cypher) == class_key(boat_class.cypher):
                return f"{other.fullname} already has the cypher '{other.cypher}'."
            if boat_class.symbol.strip() and other.symbol.strip() == boat_class.symbol.strip():
                return f"{other.fullname} already has the symbol '{other.symbol}'."
        return None

    def add(self, boat_class: BoatClass) -> None:
        """Raises ValueError (with the reason) if the class cannot be added."""
        problem = self.check(boat_class)
        if problem:
            raise ValueError(problem)
        self.classes.append(boat_class)

    def replace(self, index: int, boat_class: BoatClass) -> None:
        """Raises ValueError (with the reason) if the class cannot replace classes[index]."""
        problem = self.check(boat_class, ignore=index)
        if problem:
            raise ValueError(problem)
        self.classes[index] = boat_class

    def remove(self, index: int) -> BoatClass:
        return self.classes.pop(index)
