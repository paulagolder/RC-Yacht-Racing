"""limits.py - how big things may be, and the defaults for new race days.

DEFAULT_RACES and DEFAULT_ROWS can be changed in ~/.pyraceresults/properties.xml (see
storage/settings_store.py), within these limits.
"""

MAX_RACES = 6        # races (table columns) in one race day
MAX_PLACES = 15      # finishing places (table rows) in one race
MAX_RACE_DAYS = 15   # race days in one competition
DEFAULT_RACES = 4    # races a new race day starts with (the window can add up to MAX_RACES)
DEFAULT_ROWS = 5     # rows the race day window shows for an empty race day
MIN_YEAR, MAX_YEAR = 1900, 2200
