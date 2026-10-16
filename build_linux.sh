#!/usr/bin/env bash
# Build a single Linux program file: dist/pyraceresults
#
#     ./build_linux.sh
#
# Needs PyInstaller (pipx install pyinstaller) and tkinter (sudo apt install python3-tk).
# The program runs on this Linux version and newer ones, so build on the oldest you need.
# Data is not part of the program: each user's competitions stay in ~/.pyraceresults.

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

echo
echo "Done: $(pwd)/dist/pyraceresults"
echo "Copy it anywhere (for example ~/.local/bin) and run it."
