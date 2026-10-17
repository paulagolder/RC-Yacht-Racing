# Security check

The program was checked with [Bandit](https://bandit.readthedocs.io/), the standard security
checker for Python code (from the Python Code Quality Authority). Run it again at any time:

    pipx install bandit        # once
    ./security_check.sh        # writes the report into the output folder, in security/

## What the program does outside its own files

- It uses only Python's standard library: no third-party packages are installed or bundled.
- It does not use the network: there is no `socket`, `urllib`, `requests` or `http` in the code.
  It does not run code it reads (`eval`, `exec`, `pickle`).
- It reads and writes its XML files in `~/.pyraceresults`, and writes exported pages and reports
  in the output folder (`properties.xml`, default `~/Documents/raceresult_output`).
- It makes a `.bak` copy of a file before replacing it (`app/storage/xml_file.py`).
- After **Export HTML** it opens the page in the web browser (`app/ui/browser.py`).

## Bandit's findings, and what they mean

**Reading XML (B405, B314).** Python's XML reader can be attacked with a crafted file (an "XML
bomb", which expands until the computer runs out of memory). Every XML file is read through
`parse_xml` in `app/storage/xml_file.py`, which refuses any file with a `<!DOCTYPE>` or
`<!ENTITY>` declaration, the only way such attacks work (the program's own files never have
one), and any file that is not UTF-8. Those lines are marked `# nosec` with this reason, so
Bandit lists them as skipped rather than as issues. `tests/storage/test_xml_file.py` checks
that a bomb is refused by every reader.

**Running another program (B404, B603, Low).** `app/ui/browser.py` runs `xdg-open` to show an
exported page in the web browser. It is called with a fixed program name and the page's path,
and without a shell, so nothing typed into the program can change what is run. These are left
visible in the report for a reader to see.

## What a clean report does and does not show

Bandit looks for risky patterns in code. A clean report means no dangerous calls are hidden in
the code; it cannot prove the program only does what this file says. For that, the code is
small enough (about 3,800 lines of Python in `app/`) for anyone who reads Python to look over.
