import contextlib
import datetime
import io
import re
import unittest

import main
from app import __version__, __version_date__


class VersionTests(unittest.TestCase):
    def test_version_and_date(self):
        self.assertRegex(__version__, r"^\d+\.\d+$")
        datetime.date.fromisoformat(__version_date__)                 # a real date

    def test_version_option(self):
        for option in ("--version", "-V"):
            out = io.StringIO()
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
                main.main([option])
            self.assertEqual(ctx.exception.code, 0)
            self.assertTrue(re.fullmatch(r"pyraceresults \S+ \(\d{1,2} \w+ \d{4}\)\n", out.getvalue()),
                            out.getvalue())


if __name__ == "__main__":
    unittest.main()
