from abc import ABC, abstractmethod

from tool_use_package.tools.search.base_search_tool import BaseSearchResult
from tool_use_package.tools.search.vector_search.embedders.base_embedder import Embedding

#########################################################
## BaseVectorStore: An interface to a vector store that can upsert embeddings and run queries
#########################################################

class BaseVectorStore(ABC):
    """
    An interface to a vector store that can upsert embeddings and run queries.
    """
    
    @abstractmethod
    def upsert(self, embeddings: list[Embedding]) -> None:
        """
        Upserts a list of embeddings into the vector store.

        :param embeddings: The embeddings to upsert.
        """
        raise NotImplementedError()

    @abstractmethod
    def query(self, query_embedding: Embedding, n_search_results_to_use: int = 10) -> list[BaseSearchResult]:
        """
        Runs a query using the vector store and returns the results.

        :param query_embedding: The embedding to query with.
        :param n_search_results_to_use: The number of results to return.
        """
        raise NotImplementedError()