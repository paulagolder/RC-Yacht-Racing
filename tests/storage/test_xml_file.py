import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from app.storage.competition_store import load_competition
from app.storage.errors import StorageError
from app.storage.member_store import MEMBERS_FILE, load_members
from app.storage.settings_store import PROPERTIES_FILE, load_settings
from app.storage.xml_file import parse_xml

BOMB = """<?xml version="1.0"?>
<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>
<sails>&lol2;</sails>"""


class ParseXmlTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, name: str, data: bytes) -> Path:
        path = self.dir / name
        path.write_bytes(data)
        return path

    def test_reads_a_normal_file(self):
        path = self.write("a.xml", '<?xml version="1.0" encoding="utf-8"?><a b="é"><c/></a>'.encode())
        root = parse_xml(path)
        self.assertEqual((root.tag, root.get("b"), len(root)), ("a", "é", 1))

    def test_refuses_doctype_and_entity_declarations(self):
        for text in (BOMB, '<!doctype a><a/>', '<a><!ENTITY x "y"></a>', '<!  DOCTYPE a><a/>'):
            with self.subTest(text=text), self.assertRaises(ET.ParseError) as ctx:
                parse_xml(self.write("a.xml", text.encode()))
            self.assertIn("not allowed", str(ctx.exception))

    def test_refuses_files_that_are_not_utf8(self):
        with self.assertRaises(ET.ParseError):
            parse_xml(self.write("a.xml", BOMB.encode("utf-16")))

    def test_every_reader_refuses_a_bomb(self):
        self.write(MEMBERS_FILE, BOMB.encode())
        with self.assertRaises(StorageError):
            load_members(self.dir)
        with self.assertRaises(StorageError):
            load_competition(self.write("x.cxml", BOMB.replace("sails", "competition").encode()))
        self.write(PROPERTIES_FILE, BOMB.replace("sails", "properties").encode())
        self.assertEqual(load_settings(self.dir).default_rows, 5)       # falls back to defaults


if __name__ == "__main__":
    unittest.main()
