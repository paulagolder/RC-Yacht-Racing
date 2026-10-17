RC Yacht Racing - portable copy
===============================

For whoever sets up or looks after the USB stick. The RC-Yacht-Racing folder holds everything
the program needs:

    pyraceresults        the program (Linux). Double-click it, or run it from a terminal.
    output/              the web pages you export: results, race days, reports.
                         This is the only folder you need to open.
    system/              the program's own files: settings, club sailors, competitions.
                         Leave this folder alone; the program looks after it.

Keep the three together: copy or back up the whole RC-Yacht-Racing folder.
Close the program before you unplug the USB stick.

If the program will not start
-----------------------------
Some Linux systems do not let programs run straight from a USB stick. Open a terminal and run

    bash /path/to/RC-Yacht-Racing/system/start-linux.sh

(drag start-linux.sh into the terminal window to type its path). It copies the program to a
temporary folder, runs it from there with the data on the stick, and tidies up afterwards.

In the Files app, double-clicking may open the program as a document instead of running it:
right-click it and choose "Run as a Program".
