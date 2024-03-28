import os

# Import the requisite ToolUser class
from ....tool_user import ToolUser

# Import the embedder we will use for our search tool
from .embedders.huggingface import HuggingFaceEmbedder
from .constants import DEFAULT_EMBEDDER

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from ..base_search_tool import BaseSearchResult, BaseSearchTool

# Vector DB Searcher
class VectorSearchTool(BaseSearchTool):

    def __init__(self,
                  name,
                  description,
                  parameters,
                  vector_store,
                  embedder = None):
        """
        :param name: The name of the tool.
        :param description: The description of the tool.
        :param parameters: The parameters for the tool.
        :param vector_store: The vector store to use for searching.
        :param embedder: The name of the embedder model to use. Defaults to a HuggingFace embedder with the model "sentence-transformers/paraphrase-MiniLM-L6-v2".
        """
        super().__init__(name, description, parameters)

        if embedder is None:
            # Get your HuggingFace API key from https://huggingface.co/docs/api-inference/quicktour
            embedder = HuggingFaceEmbedder(os.environ["HUGGINGFACE_API_KEY"], DEFAULT_EMBEDDER)
        self.embedder = embedder
        self.vector_store = vector_store

    def raw_search(self, query: str, n_search_results_to_use: int) -> list[BaseSearchResult]:
        print("Query: ", query)
        print("Searching...")
        query_embedding = self.embedder.embed(query)
        search_results = self.vector_store.query(query_embedding, n_search_results_to_use=n_search_results_to_use)
        return search_results
