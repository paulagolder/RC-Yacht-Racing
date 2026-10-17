"""boat_class.py - boat classes, such as DF95 or IOM.

A class is just text, so any class can be used. Classes are matched ignoring case and spaces:
"DF95", "df95" and "DF 95" are the same class.
"""

# Suggestions for the class boxes on screen.
BOAT_CLASSES = ["DF95", "Victoria", "IOM", "Marblehead"]


def class_key(boat_class: str) -> str:
    """The form used to compare classes: 'Df 95' -> 'DF95'."""
    return "".join(boat_class.split()).upper()
