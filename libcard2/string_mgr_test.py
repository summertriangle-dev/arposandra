import unittest
import unittest.mock
import sqlite3
import os

import string_mgr


class TestTopLevel(unittest.TestCase):
    def test_batches(self):
        self.assertEqual(tuple(string_mgr.batches([1, 2, 3], groups_of=3)), ([1, 2, 3],))
        self.assertEqual(tuple(string_mgr.batches([1, 2, 3], groups_of=2)), ([1, 2], [3]))
        self.assertEqual(tuple(string_mgr.batches([1, 2, 3], groups_of=1)), ([1], [2], [3]))

    def test_bucketize(self):
        dataset = ["k1.v1", "k1.v2", "k2.v1"]
        self.assertDictEqual(string_mgr.bucketize(dataset), {"k1": ["v1", "v2"], "k2": ["v1"]})


class TestDictionaryAccess(unittest.TestCase):
    def get_DA_instance(self):
        da = string_mgr.DictionaryAccess("dummy")
        db_k = sqlite3.connect(":memory:")
        db_k.executescript(
            """
        CREATE TABLE m_dictionary(
            id TEXT NOT NULL,
            message TEXT NOT NULL,
            PRIMARY KEY (id)
        );
        INSERT INTO m_dictionary VALUES ('string1', 'helloworld');
        INSERT INTO m_dictionary VALUES ('string2', 'goodbyeworld');
        INSERT INTO m_dictionary VALUES ('string3', 'unused');
        """
        )
        db_j = sqlite3.connect(":memory:")
        db_j.executescript(
            """
        CREATE TABLE m_dictionary(
            id TEXT NOT NULL,
            message TEXT NOT NULL,
            PRIMARY KEY (id)
        );
        INSERT INTO m_dictionary VALUES ('string1', 'wwwwww');
        INSERT INTO m_dictionary VALUES ('string2', 'sdsfhdfh');
        INSERT INTO m_dictionary VALUES ('string3', 'etuiths');
        """
        )
        da.sqlites = {"k": db_k, "j": db_j}
        return da

    def test_lookup_multidict(self):
        da = self.get_DA_instance()
        self.assertDictEqual(
            da.lookup_strings(["k.string1", "k.string2", "j.string1"]),
            {"k.string1": "helloworld", "k.string2": "goodbyeworld", "j.string1": "wwwwww"},
        )

    def test_lookup_missing(self):
        da = self.get_DA_instance()
        self.assertDictEqual(da.lookup_strings(["k.empty"]), {})

    def test_getdict(self):
        with unittest.mock.patch("string_mgr.sqlite3") as the_mock:
            da = string_mgr.DictionaryAccess("mock_path")
            da.get_dictionary_handle("t")
            the_mock.connect.assert_called_with(
                "file:{0}?mode=ro".format(os.path.join("mock_path", "dictionary_ja_t.db")), uri=True
            )


if __name__ == "__main__":
    unittest.main()
