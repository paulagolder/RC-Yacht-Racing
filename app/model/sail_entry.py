"""sail_entry.py - what is typed for a finisher, and which club sailor it means.

A race day is open to all its competition's classes, so a sail number on its own may be more
than one eligible sailor's. An entry can carry tags that say which:

    12          the sail number; enough if only one eligible sailor has it
    12@         a class tag: the class's symbol (yachtclasses.xml). Used when the choices are
                the same sailor in different classes.
    12/PAG      a sailor tag (Sailor.tag). Used when the choices are different sailors.
    12@/PAG     both, if neither alone tells the choices apart.

SailResolver knows the eligible classes, the clubs and the club sailors. It finds the sailor an
entry means, gives the tagged entries to choose from when a plain number is ambiguous, and
checks a race day's results.
"""

from __future__ import annotations

from dataclasses import dataclass

from .boat_class import BoatClass, class_key
from .member_list import MemberList
from .race import Race
from .sail_number import sail_key
from .sailor import Sailor

TAG_SEPARATOR = "/"

Problem = tuple[int, int, str]      # (row, race index, message), counting from 0


@dataclass(frozen=True)
class SailEntry:
    number: str                     # the sail number as typed, without tags
    class_symbol: str = ""
    sailor_tag: str = ""

    @property
    def text(self) -> str:
        tag = f"{TAG_SEPARATOR}{self.sailor_tag}" if self.sailor_tag else ""
        return f"{self.number}{self.class_symbol}{tag}"

    @property
    def tagged(self) -> bool:
        return bool(self.class_symbol or self.sailor_tag)


class SailResolver:
    def __init__(self, members: MemberList | None, classes: list[BoatClass],
                 clubs: list[str] | None = None):
        self.members = members
        self.classes = list(classes)            # the eligible classes
        self.clubs = list(clubs or [])          # none: any club
        self._symbols = {c.symbol.strip(): c for c in self.classes if c.symbol.strip()}

    @property
    def class_names(self) -> list[str]:
        return [c.fullname for c in self.classes]

    # -- reading an entry -------------------------------------------------------------------

    def parse(self, text: str) -> SailEntry:
        """'12@/pag' -> SailEntry('12', '@', 'PAG'). A last character is only a class tag if it
        is the symbol of one of the eligible classes."""
        text = text.strip()
        number, _, tag = text.partition(TAG_SEPARATOR)
        number = number.strip()
        symbol = ""
        if len(number) > 1 and number[-1] in self._symbols:
            number, symbol = number[:-1].strip(), number[-1]
        return SailEntry(number, symbol, tag.strip().upper())

    def class_of(self, sailor: Sailor) -> BoatClass | None:
        """The eligible class a sailor's boat is in (sailors' files name a class by its full
        name or its key)."""
        wanted = class_key(sailor.boat_class)
        return next((c for c in self.classes
                     if wanted in (class_key(c.key), class_key(c.fullname))), None)

    def class_name(self, sailor: Sailor) -> str:
        boat_class = self.class_of(sailor)
        return boat_class.fullname if boat_class else sailor.boat_class

    def candidates(self, text: str) -> list[Sailor]:
        """Every eligible sailor the entry could mean: its sail number in an eligible class,
        from one of the clubs, and matching any tags."""
        if self.members is None:
            return []
        entry = self.parse(text)
        if not entry.number:
            return []
        classes = [self._symbols[entry.class_symbol]] if entry.class_symbol else self.classes
        found = []
        for boat_class in classes:
            for name in dict.fromkeys((boat_class.fullname, boat_class.key)):
                sailor = self.members.find(entry.number, name, self.clubs)
                if sailor is not None and sailor not in found:
                    found.append(sailor)
        if entry.sailor_tag:
            found = [s for s in found if s.tag == entry.sailor_tag]
        return found

    def sailor(self, text: str) -> Sailor | None:
        """The one sailor the entry means, or None if it is unrecognised or ambiguous."""
        found = self.candidates(text)
        return found[0] if len(found) == 1 else None

    def choices(self, text: str) -> list[tuple[str, Sailor]]:
        """(tagged entry, sailor) for each sailor an ambiguous entry could mean; empty if it is
        not ambiguous. Each entry carries the fewest tags that tell the choices apart: the
        sailor tag if the choices are different sailors, the class tag if they are one sailor
        in different classes, both if neither alone will do."""
        found = self.candidates(text)
        if len(found) < 2:
            return []
        number = self.parse(text).number
        options = []
        for sailor in found:
            symbol = (self.class_of(sailor) or BoatClass("", "")).symbol.strip()
            for entry in (SailEntry(number, "", sailor.tag), SailEntry(number, symbol, ""),
                          SailEntry(number, symbol, sailor.tag)):
                if entry.tagged and self.candidates(entry.text) == [sailor]:
                    options.append((entry.text, sailor))
                    break
            else:
                options.append(("", sailor))        # cannot be told apart (no class symbol)
        return options

    def describe(self, sailor: Sailor) -> str:
        """'12: Ann Smith (DF65, RMBC)'."""
        return f"{sailor.number}: {sailor.name} ({self.class_name(sailor)}, {sailor.club})"

    def boat_key(self, text: str) -> tuple[str, str]:
        """The same boat, however it was typed: its class and sail number when it is known."""
        sailor = self.sailor(text)
        return sailor.key if sailor else ("", sail_key(self.parse(text).number))

    # -- checking a race day ----------------------------------------------------------------

    def check_races(self, races: list[Race]) -> list[Problem]:
        """Problems in a race day's results, in table order. Empty places are allowed.

        A finish is wrong if it is no eligible sailor's (unrecognised), if it could be more than
        one sailor's and has not been tagged to say which (ambiguous), if the same boat is
        already further up the race, or if the sailor is already further up the race with
        another of their boats (a sailor sails one boat at a time).
        """
        if self.members is None:
            return []
        classes = " or ".join(self.class_names)
        from_clubs = f" from {', '.join(self.clubs)}" if self.clubs else ""
        problems = []
        for c, race in enumerate(races):
            boats: dict[tuple[str, str], int] = {}               # boat -> row first seen
            sailing: dict[str, tuple[int, str]] = {}             # person -> (row, entry)
            for place, value in race.places():
                r = place - 1
                found = self.candidates(value)
                if not found:
                    problems.append((r, c, f"Unrecognised sail '{value}': no {classes} "
                                           f"sailor{from_clubs} has it."))
                    continue
                if len(found) > 1:
                    names = "; ".join(self.describe(s) for s in found)
                    problems.append((r, c, f"Sail '{value}' could be {names}. Choose which."))
                    continue
                sailor = found[0]
                if sailor.key in boats:
                    problems.append((r, c, f"Sail '{value}' is already in row "
                                           f"{boats[sailor.key] + 1} of this race."))
                    continue
                boats[sailor.key] = r
                if sailor.same_person in sailing:
                    row, entry = sailing[sailor.same_person]
                    problems.append((r, c, f"{sailor.name} is already sailing {entry} in "
                                           f"row {row + 1} of this race."))
                else:
                    sailing[sailor.same_person] = (r, value.strip())
        return sorted(problems)
