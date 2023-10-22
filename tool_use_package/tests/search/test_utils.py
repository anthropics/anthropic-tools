import unittest
from unittest.mock import MagicMock, patch, mock_open

from ...tools.search.vector_search.utils import chunk_document, embed_and_upload, Document
from ...tools.search.vector_search.embedders.base_embedder import BaseEmbedder
from ...tools.search.vector_search.vectorstores.base_vector_store import BaseVectorStore

class TestChunkDocument(unittest.TestCase):

    def test_empty_document(self):
        document = Document(text="")
        result = chunk_document(document, 5)
        self.assertEqual(len(result), 0)

    def test_tokens_per_chunk_larger_than_document(self):
        document = Document(text="This is a test.")
        result = chunk_document(document, 100)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "This is a test.")
        self.assertEqual(result[0].metadata, document.metadata)

    def test_tokens_per_chunk_equal_to_document(self):
        document = Document(text="This is a test.")
        result = chunk_document(document, 5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "This is a test.")
        self.assertEqual(result[0].metadata, document.metadata)

    def test_tokens_per_chunk_smaller_than_document(self):
        document = Document(text="This is a test.", metadata={"id": 1})
        result = chunk_document(document, 2)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].text, "This is")
        self.assertEqual(result[1].text, " a test")
        self.assertEqual(result[2].text, ".")
        self.assertEqual(result[0].metadata, document.metadata)
        self.assertEqual(result[1].metadata, document.metadata)
        self.assertEqual(result[2].metadata, document.metadata)

    def test_tokens_per_chunk_smaller_than_document_with_stride(self):
        document = Document(text="This is a test.", metadata={"id": 1})
        result = chunk_document(document, 3, stride=2)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].text, "This is a")
        self.assertEqual(result[1].text, " a test.")
        self.assertEqual(result[2].text, ".")

class TestEmbedAndUpload(unittest.IsolatedAsyncioTestCase):
    def test_embed_and_upload(self):
        input_file = "test.jsonl"
        vectorstore = MagicMock(spec=BaseVectorStore)
        embedder = MagicMock(spec=BaseEmbedder)

        with patch("builtins.open", mock_open(read_data='{"text": "Sample text", "metadata": {"id": 1}}\n')) as mock_file:
            with patch("tool_use_package.tools.search.vector_search.utils.chunk_document") as mock_chunk_document:
                mock_chunk_document.return_value = [Document(text="Sample text", metadata={"id": 1})]

                embed_and_upload(input_file, vectorstore, embedder, tokens_per_chunk=4, stride=2, batch_size=1)

                mock_file.assert_called_once_with(input_file, "r")
                mock_chunk_document.assert_called_once()
                embedder.embed_batch.assert_called_once_with(["Sample text"])
                vectorstore.upsert.assert_called_once()

if __name__ == "__main__":
    unittest.main()
