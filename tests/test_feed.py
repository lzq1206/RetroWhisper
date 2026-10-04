import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import fetch_repositories as feed


def repository(name, stars=100):
    return {"full_name": name, "name": name.split("/")[-1], "description": "retro arcade game", "stargazers_count": stars, "updated_at": "2026-10-03T00:00:00Z"}


class FeedTests(unittest.TestCase):
    def test_appends_ten_without_truncating_history(self):
        old = {"updated_at": "2026-09-16T00:00:00Z", "items": [{"full_name": "old/game"}]}
        candidates = {str(i): repository(f"retro/game{i}") for i in range(25)}
        result = feed.merge_repositories(old, candidates, "2026-10-04T00:00:00Z")
        self.assertEqual(len(result["items"]), 11)
        self.assertEqual(result["last_batch_count"], 10)
        self.assertEqual(result["items"][-1]["full_name"], "old/game")
        self.assertEqual(result["items"][-1]["first_seen_at"], old["updated_at"])
        again = feed.merge_repositories(result, candidates, "2026-10-05T00:00:00Z")
        self.assertEqual(len(again["items"]), 21)
        self.assertEqual(len({x["full_name"].lower() for x in again["items"]}), 21)

    def test_refresh_preserves_collection_time_and_case_insensitive_identity(self):
        old = {"items": [{"full_name": "Retro/Game", "first_seen_at": "2026-09-01T00:00:00Z"}]}
        result = feed.merge_repositories(old, {"game": repository("retro/game", 999)}, "2026-10-04T00:00:00Z")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["last_batch_count"], 0)
        self.assertEqual(result["items"][0]["stars"], 999)
        self.assertEqual(result["items"][0]["first_seen_at"], "2026-09-01T00:00:00Z")

    def test_few_candidates_and_page_wrap(self):
        result = feed.merge_repositories({"search_page": 10}, {"a": repository("retro/a")}, "2026-10-04T00:00:00Z")
        self.assertEqual(result["last_batch_count"], 1)
        self.assertEqual(result["search_page"], 1)
        self.assertEqual(result["refresh_hours"], 6)

    def test_failed_fetch_leaves_file_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repositories.json"
            path.write_text('{"updated_at":"old","items":[]}', encoding="utf-8")
            before = path.read_bytes()
            with patch.object(feed, "DATA_FILE", path), patch.object(feed, "fetch_repo", return_value=None), patch.object(feed, "search_repositories", return_value=[]):
                self.assertEqual(feed.main(), 1)
            self.assertEqual(path.read_bytes(), before)

    def test_corrupt_history_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repositories.json"
            path.write_text("broken json", encoding="utf-8")
            with patch.object(feed, "DATA_FILE", path), self.assertRaises(json.JSONDecodeError):
                feed.load_existing()

    def test_newest_batch_and_repository_activity_order(self):
        candidates = {"a": repository("retro/a"), "b": {**repository("retro/b"), "updated_at": "2026-10-04T00:00:00Z"}}
        result = feed.merge_repositories({}, candidates, "2026-10-05T00:00:00Z")
        self.assertEqual([x["full_name"] for x in result["items"]], ["retro/b", "retro/a"])


if __name__ == "__main__":
    unittest.main()
