from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..base_search_tool import BaseSearchResult

#########################################################
## Embedder: Convert texts to embeddings
#########################################################

@dataclass
class Embedding:
    """
    An embedding of a text, along with the text itself and any metadata associated with it.
    """
    embedding: list[float]
    text: str


class Embedder(ABC):
    """
    An embedder that can embed a single text or a batch of texts.
    """
    dim: int
    
    @abstractmethod
    def embed(self, text: str) -> Embedding:
        """
        Embeds a single text.

        :param text: The text to embed.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[Embedding]:
        """
        Embeds a batch of texts.

        :param texts: The texts to embed.
        """
        raise NotImplementedError()
    
#########################################################
## VectorStore: An interface to a vector store that can upsert embeddings and run queries
#########################################################

class VectorStore(ABC):
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