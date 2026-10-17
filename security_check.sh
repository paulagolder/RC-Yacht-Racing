#!/usr/bin/env bash
# Check the program's code with Bandit and write the report into the output folder:
#
#     ./security_check.sh            # output folder from ~/.pyraceresults/properties.xml
#     ./security_check.sh some/dir   # or here
#
# Needs Bandit (pipx install bandit). Writes, in <output folder>/security/:
#     bandit_report.html   the full report, to open in a web browser
#     bandit_report.txt    the same as text
#     security_notes.md    what the findings mean (a copy of SECURITY.md)

set -euo pipefail
cd "$(dirname "$0")"

bandit=$(command -v bandit || echo "$HOME/.local/bin/bandit")
if [ ! -x "$bandit" ]; then
    echo "Bandit is not installed: pipx install bandit" >&2
    exit 1
fi

if [ $# -gt 0 ]; then
    out="$1"
else
    out="$(python3 -c 'from app.storage.settings_store import load_settings; print(load_settings().output_dir)')/security"
fi
mkdir -p "$out"

# Bandit exits with 1 when it reports anything (even Low), so carry on and show the summary.
"$bandit" -r app main.py -f html -o "$out/bandit_report.html" -q || true
"$bandit" -r app main.py -f txt -o "$out/bandit_report.txt" -q || true
cp SECURITY.md "$out/security_notes.md"

sed -n '/^Run metrics:/,$p' "$out/bandit_report.txt"
echo
echo "Report: $out/bandit_report.html"
echo "Notes:  $out/security_notes.md"
