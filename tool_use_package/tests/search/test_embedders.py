import os

import unittest

from ...tools.search.vector_search.embedders.base_embedder import Embedding
from ...tools.search.vector_search.embedders.huggingface import HuggingFaceEmbedder


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

class TestHuggingFaceEmbedder(unittest.TestCase):
    def setUp(self):
        self.api_key = os.environ["HUGGINGFACE_API_KEY"]
        assert self.api_key is not None, "HUGGINGFACE_API_KEY is not set."
        self.embedder = HuggingFaceEmbedder(api_key=self.api_key, model_name=DEFAULT_EMBEDDING_MODEL)

    def test_embed(self):
        query = "This is a test sentence."
        result = self.embedder.embed(query)
        self.assertIsInstance(result, Embedding)
        self.assertEqual(result.text, query)
        self.assertIsInstance(result.embedding, list)

    def test_embed_batch(self):
        queries = ["This is a test sentence.", "Another test sentence."]
        results = self.embedder.embed_batch(queries)
        self.assertIsInstance(results, list)
        for result, query in zip(results, queries):
            self.assertIsInstance(result, Embedding)
            self.assertEqual(result.text, query)
            self.assertIsInstance(result.embedding, list)

if __name__ == "__main__":
    unittest.main()
