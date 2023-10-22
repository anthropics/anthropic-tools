import os
import unittest

from ...tools.search.base_search_tool import BaseSearchResult
from ...tools.search.vector_search.vector_search_tool import VectorSearchTool
from ...tools.search.wikipedia_search_tool import WikipediaSearchTool
from ...tools.search.brave_search_tool import BraveSearchTool
from ...tools.search.elasticsearch_search_tool import ElasticsearchSearchTool

class TestVectorSearch(unittest.TestCase):

    def setUp(self):
        self.vector_store = self.setup_pinecone()
        self.searchtool = VectorSearchTool(name="test", 
                                            description="This is a test search tool.",
                                            parameters=[
                                                {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
                                                {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is an Amazon product."}
                                            ],
                                            vector_store=self.vector_store,
                                            embedder=None)

    def setup_pinecone(self):
        # Import the vector store we will use for our search tool
        import pinecone
        from ...tools.search.vector_search.vectorstores.pinecone import PineconeVectorStore
        from ...tools.search.vector_search.utils import embed_and_upload

        # Initialize Pinecone and create a vector store. Get your Pinecone API key from https://www.pinecone.io/start/
        PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
        PINECONE_ENVIRONMENT = os.environ["PINECONE_ENVIRONMENT"]
        PINECONE_DATABASE = "test-index"

        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        if PINECONE_DATABASE not in pinecone.list_indexes():
            print("No remote vectorstore found.")

            batch_size = 128
            input_file = "tool_use_package/tests/search/data/local_db.jsonl"
            print("Creating new index and filling it from local text files. This may take a while...")
            pinecone.create_index(PINECONE_DATABASE, dimension=768, metric="cosine")
            vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
            embed_and_upload(input_file, vector_store, batch_size=batch_size)
        else:
            vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
        return vector_store

    def test_search(self):
        query = "products"
        n_search_results_to_use = 2
        search_results = self.searchtool.raw_search(query, n_search_results_to_use)
        self.assertIsInstance(search_results, list)
        self.assertEqual(len(search_results), n_search_results_to_use)
        for result in search_results:
            self.assertIsInstance(result, BaseSearchResult)
            self.assertIsInstance(result.content, str)

class TestWikipediaSearch(unittest.TestCase):

    def setUp(self):
        self.searchtool = WikipediaSearchTool(name="test", 
                                            description="This is a test search tool.",
                                            parameters=[
                                                {"name": "query", "type": "str", "description": "The search term to enter into the Wikipedia search engine. Remember to use broad topic keywords."},
                                                {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is a Wikipedia page."}
                                            ])
    def test_search(self):
        query = "This is a test sentence."
        n_search_results_to_use = 2
        search_results = self.searchtool.raw_search(query, n_search_results_to_use)
        self.assertIsInstance(search_results, list)
        self.assertEqual(len(search_results), n_search_results_to_use)
        for result in search_results:
            self.assertIsInstance(result, BaseSearchResult)
            self.assertIsInstance(result.content, str)

class TestBraveSearch(unittest.TestCase):

    def setUp(self):
        self.searchtool = BraveSearchTool(name="test", 
                                            description="This is a test search tool.",
                                            parameters=[
                                                {"name": "query", "type": "str", "description": "The search term to enter into the Brave search engine. Remember to use broad topic keywords."},
                                                {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is a website page."}
                                            ],
                                            brave_api_key=os.environ['BRAVE_API_KEY'])
    def test_search(self):
        query = "This is a test sentence."
        n_search_results_to_use = 2
        search_results = self.searchtool.raw_search(query, n_search_results_to_use)
        self.assertIsInstance(search_results, list)
        self.assertEqual(len(search_results), n_search_results_to_use)
        for result in search_results:
            self.assertIsInstance(result, BaseSearchResult)
            self.assertIsInstance(result.content, str)

class TestElasticsearchSearch(unittest.TestCase):

    def setUp(self):
        self.upload_data()
        self.searchtool = ElasticsearchSearchTool(name="test", 
                                            description="This is a test search tool.",
                                            parameters=[
                                                {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
                                                {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return."}
                                            ],
                                            elasticsearch_cloud_id=os.environ["ELASTICSEARCH_CLOUD_ID"],
                                            elasticsearch_api_key_id=os.environ["ELASTICSEARCH_API_KEY_ID"],
                                            elasticsearch_api_key=os.environ["ELASTICSEARCH_API_KEY"],
                                            elasticsearch_index="test-index")

    # Upload Amazon product data to Elasticsearch
    def upload_data(self):
        from elasticsearch import Elasticsearch
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        api_key_id = os.getenv("ELASTICSEARCH_API_KEY_ID")
        api_key = os.getenv("ELASTICSEARCH_API_KEY")

        index_name = "test-index"

        if cloud_id is None or api_key_id is None or api_key is None:
            raise ValueError("ELASTICSEARCH_CLOUD_ID, ELASTICSEARCH_API_KEY_ID, and ELASTICSEARCH_API_KEY must be set as environment variables")

        es = Elasticsearch(
                cloud_id=cloud_id,
                api_key=(api_key_id, api_key),
            )

        if not es.indices.exists(index=index_name):
            print("No remote index found. Creating new index and filling it from local text files. This may take a while...")
            from ...tools.search.vector_search.utils import upload_to_elasticsearch
            upload_to_elasticsearch(
                input_file="tool_use_package/tests/search/data/local_db.jsonl",
                index_name=index_name,
                cloud_id=cloud_id,
                api_key_id=api_key_id,
                api_key=api_key
            )
    def test_search(self):
        query = "products"
        n_search_results_to_use = 1
        search_results = self.searchtool.raw_search(query, n_search_results_to_use)
        self.assertIsInstance(search_results, list)
        self.assertEqual(len(search_results), n_search_results_to_use)
        for result in search_results:
            self.assertIsInstance(result, BaseSearchResult)
            self.assertIsInstance(result.content, str)


if __name__ == "__main__":
    unittest.main()
