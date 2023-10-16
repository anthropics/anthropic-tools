import os
from typing import Optional

# Import the requisite ToolUser class
from ...tool_user import ToolUser
from .embedders.huggingface import HuggingFaceEmbedder
from .constants import DEFAULT_EMBEDDER

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from .base_search_tool import BaseSearchResult, BaseSearchTool

import logging
logger = logging.getLogger(__name__)

# Vector DB Searcher

class VectorSearchTool(BaseSearchTool):

    def __init__(self,
                  name,
                  description,
                  parameters,
                  vector_store,
                  embedder = None):
        
        super().__init__(name, description, parameters)

        if embedder is None:
            logger.info(f"Using default embedder: {DEFAULT_EMBEDDER}")
            embedder = HuggingFaceEmbedder(os.environ["HUGGINGFACE_API_KEY"], DEFAULT_EMBEDDER)
        self.embedder = embedder
        self.vector_store = vector_store

    def raw_search(self, query: str, n_search_results_to_use: int) -> list[BaseSearchResult]:
        query_embedding = self.embedder.embed(query)
        search_results = self.vector_store.query(query_embedding, n_search_results_to_use=n_search_results_to_use)
        return search_results
    
    def process_raw_search_results(self, results: list[BaseSearchResult]) -> list[list[str]]:
        processed_search_results = [[result.source, result.content.strip()] for result in results]
        return processed_search_results


def upload_data():
    import pinecone
    from .vectorstores.pinecone import PineconeVectorStore
    from .embedders.huggingface import HuggingFaceEmbedder
    from .utils import embed_and_upload
    from .constants import DEFAULT_EMBEDDER, DEFAULT_SPARSE_EMBEDDER

    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_ENVIRONMENT = os.environ["PINECONE_ENVIRONMENT"]
    PINECONE_DATABASE = os.environ["PINECONE_DATABASE"]

    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    if PINECONE_DATABASE not in pinecone.list_indexes():
        logger.info("No remote vectorstore found. Creating new index and filling it from local text files.")

        batch_size = 128
        input_file = "data/amazon-products.jsonl"

        pinecone.create_index(PINECONE_DATABASE, dimension=768, metric="cosine")
        vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
        embed_and_upload(input_file, vector_store, batch_size=batch_size)
    else:
        vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
    return vector_store

def create_amazon_search_tool(vector_store):
    # Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters 
    tool_name = "search_amazon"
    tool_description = """The search engine will search over the Amazon Product database, and return for each product its title, description, and a set of tags."""
    tool_parameters = [
        {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
        {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is an Amazon product."}
    ]

    amazon_search_tool = VectorSearchTool(tool_name, tool_description, tool_parameters, vector_store)

    # Pass the tool instance into the ToolUser
    tool_user = ToolUser([amazon_search_tool])
    return tool_user

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    vector_store = upload_data()
    tool_user = create_amazon_search_tool(vector_store)
    print(tool_user.use_tools("I want to get my daughter more interested in science. What kind of gifts should I get her?", verbose=True, single_function_call=False))