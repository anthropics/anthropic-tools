import pinecone
from more_itertools import chunked

from .base_vector_store import BaseVectorStore
from tool_use_package.tools.search.vector_search.embedders.base_embedder import Embedding
from ...base_search_tool import BaseSearchResult

import logging
logger = logging.getLogger(__name__)


############################################
# Pinecone VectorStore implementations
############################################

class PineconeVectorStore(BaseVectorStore):
    '''
    Pinecone vectorstores maintain a single embedding matrix.
    
    How it works:
    - On init, the Pinecone index is loaded (this assumes that the Pinecone index already exists).
    - When upserting embeddings, the embeddings are upserted into the Pinecone index.
    -- The embeddings are stored as a list of ids, vectors, and metadatas. Metadatas are used to store the text data for each embedding; Pinecone indices do not store text data by default.
    -- The ids are the index of the embedding in the Pinecone index.
    - When querying, the query embedding is compared to all embeddings in the Pinecone index using the similarity specified when the index was created.

    Note that the vectorstore does not contain any logic for creating embeddings. It is assumed that the embeddings are created elsewhere
    using Embedders and passed to the vectorstore for storage and retrieval. The utils.embed_and_upload() is a wrapper to help do this.
    '''
    def __init__(self, api_key: str, environment: str, index: str):
        self.api_key = api_key
        self.environment = environment
        self.index = index
        self.pinecone_index = self._init_pinecone_index()
        self.pinecone_index_dimensions = self.pinecone_index.describe_index_stats().dimension

    def _init_pinecone_index(self):
        pinecone.init(
            api_key=self.api_key,
            environment=self.environment,
        )
        if self.index not in pinecone.list_indexes():
            raise ValueError(f"Pinecone index {self.index} does not exist")
        return pinecone.Index(self.index)

    def query(self, query_embedding: Embedding, n_search_results_to_use: int = 10) -> list[BaseSearchResult]:
        if len(query_embedding.embedding) != self.pinecone_index_dimensions:
            raise ValueError(f"Query embedding dimension {len(query_embedding.embedding)} does not match Pinecone index dimension {self.pinecone_index_dimensions}")
        results = self.pinecone_index.query(
            vector=query_embedding.embedding, top_k=n_search_results_to_use, include_metadata=True
        )
        results=[BaseSearchResult(source=str(hash(match['metadata']['text'])), content=match['metadata']['text']) for match in results.matches]
        return results

    def upsert(self, embeddings: list[Embedding], upsert_batch_size: int = 128) -> None:
        '''
        This method upserts embeddings into the Pinecone index in batches of size upsert_batch_size.

        Since Pinecone indices uniquely identify embeddings by their ids,
        we need to keep track of the current index size and update the id counter correspondingly.
        '''
        embedding_chunks = chunked(embeddings, n=upsert_batch_size) # split embeddings into chunks of size upsert_batch_size
        current_index_size = self.pinecone_index.describe_index_stats()['total_vector_count'] # get the current index size from Pinecone
        i = 0 # keep track of the current index in the current batch
        for emb_chunk in embedding_chunks:
            # for each chunk of size upsert_batch_size, create a list of ids, vectors, and metadatas, and upsert them into the Pinecone index
            ids = [str(current_index_size+1+i) for i in range(i,i+len(emb_chunk))]
            vectors = [emb.embedding for emb in emb_chunk]
            metadatas = [{'text': emb.text} for emb in emb_chunk]
            records = list(zip(ids, vectors, metadatas))
            self.pinecone_index.upsert(vectors=records)
            i += len(emb_chunk) 
