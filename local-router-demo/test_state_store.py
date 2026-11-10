import os
import tempfile
import unittest

from state_store import SQLiteStateStore


class SQLiteStateStoreTests(unittest.TestCase):
    def test_replay_guard_persists_across_store_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,"state.sqlite3")
            first=SQLiteStateStore(path)
            self.assertTrue(first.claim_request("request-0001"))
            second=SQLiteStateStore(path)
            self.assertFalse(second.claim_request("request-0001"))
            self.assertTrue(second.claim_request("request-0002"))

    def test_node_registration_upserts_and_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=SQLiteStateStore(os.path.join(tmp,"state.sqlite3"))
            store.register_node("PC2","http://192.168.1.20:8101",["text_stats"])
            store.register_node("PC2","http://192.168.1.21:8101",["echo"])
            nodes=store.list_nodes()
            self.assertEqual(len(nodes),1)
            self.assertEqual(nodes[0]["url"],"http://192.168.1.21:8101")
            self.assertEqual(nodes[0]["capabilities"],["echo"])


if __name__=="__main__":
    unittest.main()
