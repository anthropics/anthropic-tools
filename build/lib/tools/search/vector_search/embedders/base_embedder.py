from dataclasses import dataclass
from abc import ABC, abstractmethod

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


class BaseEmbedder(ABC):
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
    