#!/usr/bin/env python3
"""Self-checks for the pipeline helpers. Run: python3 -m unittest discover langpacks/scripts"""
import unittest

from common import check_file, item_id, make_id, normalize
from validate import similarity, validate


class PipelineTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("  Hello,   WORLD! "), "hello world")
        self.assertEqual(normalize("Café"), normalize("Café"))  # NFC

    def test_word_id_ignores_ipa_for_english_only(self):
        a = {"lang": "en", "kind": "word", "text": "run", "partOfSpeech": "verb", "reading": "/rʌn/"}
        self.assertEqual(item_id(a), item_id({**a, "reading": "/ɹʌn/"}))
        self.assertNotEqual(item_id(a), item_id({**a, "partOfSpeech": "noun"}))
        ja = {"lang": "ja", "kind": "word", "text": "上手", "partOfSpeech": "adj"}
        self.assertNotEqual(item_id({**ja, "reading": "じょうず"}), item_id({**ja, "reading": "うわて"}))

    def test_sentence_id_ignores_case_and_punctuation(self):
        self.assertEqual(make_id("en", "sentence", "Hi there!"), make_id("en", "sentence", "hi there"))

    def test_schema_checker(self):
        good = {"id": make_id("en", "sentence", "Hi"), "lang": "en", "kind": "sentence", "text": "Hi", "level": "A1"}
        self.assertEqual(check_file(good, "item.schema.json"), [])
        bad = {**good, "level": "Z9", "extra": 1}
        bad.pop("text")
        errs = " ".join(check_file(bad, "item.schema.json"))
        for part in ("missing text", "Z9", "unknown field extra"):
            self.assertIn(part, errs)

    def test_similarity(self):
        self.assertGreater(similarity("i like green tea", "i like green tea"), 0.9)
        self.assertLess(similarity("i like green tea", "i like black coffee"), 0.9)

    def test_repo_content_is_valid(self):
        errors, _, packs, _ = validate()
        self.assertEqual(errors, [])
        self.assertGreater(packs, 0)


if __name__ == "__main__":
    unittest.main()
