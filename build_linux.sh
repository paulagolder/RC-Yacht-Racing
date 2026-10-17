#!/usr/bin/env bash
# Build a single Linux program file, dist/pyraceresults, and a portable copy for a USB stick,
# dist/RC-Yacht-Racing/ (see portable/README.txt).
#
#     ./build_linux.sh
#
# Needs PyInstaller (pipx install pyinstaller) and tkinter (sudo apt install python3-tk).
# The program runs on this Linux version and newer ones, so build on the oldest you need.
# Data is not part of the program: each user's competitions stay in ~/.pyraceresults, or in
# the portable copy's system folder.

set -euo pipefail
cd "$(dirname "$0")"

echo "Running the tests..."
python3 -m unittest discover -s tests -t . -q

# The club logo: Tk 8.6 cannot show SVG, so the window uses a PNG made from it.
# Remade here when ImageMagick is installed; otherwise the PNG already in the project is used.
logo=app/resources/club_logo
if command -v convert >/dev/null && [ "$logo.svg" -nt "$logo.png" ]; then
    echo "Making the logo PNG..."
    convert -background none -density 384 "$logo.svg" -trim +repage -resize x56 -depth 8 "$logo.png"
fi

echo "Building..."
pyinstaller --noconfirm --clean --onefile --windowed \
    --name pyraceresults \
    --add-data "$(pwd)/app/resources:app/resources" \
    --distpath dist --workpath build --specpath build \
    main.py

# The portable copy, for a USB stick: the program and output/ on top, the rest in system/.
# system/ starts with no data; the program makes its settings there the first time it runs.
echo "Making the portable copy..."
portable=dist/RC-Yacht-Racing
rm -rf "$portable"
mkdir -p "$portable/output" "$portable/system"
cp dist/pyraceresults "$portable/"
cp portable/README.txt portable/start-linux.sh "$portable/system/"

echo
echo "Done: $(pwd)/dist/pyraceresults"
echo "Copy it anywhere (for example ~/.local/bin) and run it."
echo
echo "Portable copy: $(pwd)/$portable"
echo "Copy the whole folder to a USB stick. Add the club's files (RMBCSail.xml, properties.xml,"
echo "yachtclasses.xml, competitions) to its system folder."
