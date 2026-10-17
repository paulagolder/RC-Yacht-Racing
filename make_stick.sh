#!/usr/bin/env bash
# Put the portable copy on a USB stick, with the club's data:
#
#     ./make_stick.sh /media/$USER/STICK                    data from ~/.pyraceresults
#     ./make_stick.sh /media/$USER/STICK ~/other-data       data from another folder
#
# Makes STICK/RC-Yacht-Racing/ (see portable/README.txt):
#
#     pyraceresults        the program
#     output/              exported web pages
#     system/              settings, club sailors, boat classes, competitions
#
# Builds the program first (./build_linux.sh) if it is missing or older than the code.
#
# A new stick gets a copy of the data folder's properties.xml (exporting to output/ on the
# stick), RMBCSail.xml, yachtclasses.xml and competitions (*.cxml). A stick that already has
# a system folder only gets the new program, README and launcher: the data on it is left
# alone, as it may be newer than this computer's.

set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi
stick="${1%/}"
data="${2:-$HOME/.pyraceresults}"
portable=dist/RC-Yacht-Racing
target="$stick/RC-Yacht-Racing"

[ -d "$stick" ] && [ -w "$stick" ] || { echo "Cannot write to $stick: is the stick plugged in?" >&2; exit 1; }
[ -d "$data" ] || { echo "No data folder $data" >&2; exit 1; }

# Build if there is no program yet, or the code has changed since it was built.
if [ ! -f "$portable/pyraceresults" ] ||
   [ -n "$(find main.py app portable -newer "$portable/pyraceresults" -type f -print -quit)" ]; then
    echo "Building the program first..."
    ./build_linux.sh >/dev/null
fi

echo "Putting the program on $target ..."
mkdir -p "$target/output" "$target/system"
cp "$portable/pyraceresults" "$target/"
cp "$portable/system/README.txt" "$portable/system/start-linux.sh" "$target/system/"

if [ -n "$(find "$target/system" -maxdepth 1 \( -name '*.cxml' -o -name 'RMBCSail.xml' \) -print -quit)" ]; then
    echo "The stick already has data in system/: left as it is (program updated only)."
else
    echo "Copying the data from $data ..."
    copied=0
    for name in RMBCSail.xml yachtclasses.xml; do
        if [ -f "$data/$name" ]; then cp "$data/$name" "$target/system/"; copied=$((copied + 1)); fi
    done
    for file in "$data"/*.cxml; do
        if [ -f "$file" ]; then cp "$file" "$target/system/"; copied=$((copied + 1)); fi
    done
    if [ -f "$data/properties.xml" ]; then
        # Export onto the stick, not into a folder on whichever computer is running it.
        sed 's|<output_folder>.*</output_folder>|<output_folder>output</output_folder>|' \
            "$data/properties.xml" > "$target/system/properties.xml"
        copied=$((copied + 1))
    fi
    echo "Copied $copied files."
fi

echo "Writing everything to the stick..."
sync

echo
echo "Done: $target"
if "$target/pyraceresults" --version >/dev/null 2>&1; then
    echo "The program runs straight from the stick: double-click pyraceresults (in the Files app,"
    echo "right-click > Run as a Program if double-clicking does not start it)."
else
    fstype="$(findmnt -n -o FSTYPE --target "$target" 2>/dev/null || true)"
    echo "Note: this computer will not run programs straight from the stick${fstype:+ ($fstype)}."
    echo "Start it with:   bash \"$target/system/start-linux.sh\""
    if [ "$fstype" = vfat ]; then
        echo "Linux only runs .exe, .bat and .com files from FAT32 sticks. A stick formatted"
        echo "exFAT runs it directly, and still works on Windows."
    fi
fi
echo "Eject the stick before you unplug it."
