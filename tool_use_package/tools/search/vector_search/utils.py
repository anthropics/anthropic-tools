import os
import json
from typing import Optional
import anthropic
from dataclasses import dataclass
from tqdm import tqdm

from .constants import DEFAULT_EMBEDDER
from .embedders.base_embedder import BaseEmbedder
from .vectorstores.base_vector_store import BaseVectorStore
from .embedders.huggingface import HuggingFaceEmbedder

# Chunking and uploading
@dataclass
class Document:
    """
    A single document.
    """
    text: str
    metadata: Optional[dict] = None

# Embedding and uploading
def embed_and_upload(
        input_file: str,
        vectorstore: BaseVectorStore,
        embedder: Optional[BaseEmbedder] = None,
        tokens_per_chunk: int = 384,
        stride: Optional[int] = None,
        batch_size: int = 128) -> None:
    
    if embedder is None:
        embedder = HuggingFaceEmbedder(os.environ['HUGGINGFACE_API_KEY'], DEFAULT_EMBEDDER)

    # Load the documents
    documents: list[Document] = []
    file_type = input_file.split(".")[-1]
    if file_type == "jsonl":
        with open(input_file, "r") as f:
            for i, line in enumerate(f):
                data = json.loads(line)
                text = data["text"]
                if text is None:
                    raise ValueError(f"Invalid jsonl file. 'text' key is missing on line {i}")
                metadata = data.get("metadata", None)
                doc = Document(text=text, metadata=metadata)
                documents.append(doc)
    else:
        raise ValueError("Invalid file_type. Supported types: 'jsonl'")
    
    # Chunk the documents
    chunked_documents = []
    for document in documents:
        chunks = chunk_document(document, tokens_per_chunk, stride)
        chunked_documents += chunks

    # Embed and upload the documents
    bar = tqdm(total=len(chunked_documents), desc="Embedding and uploading documents", leave=True)
    for i in range(0, len(chunked_documents), batch_size):
        batch = chunked_documents[i:i + batch_size]
        batch_embeddings = embedder.embed_batch([doc.text for doc in batch])
        vectorstore.upsert(batch_embeddings)
        bar.update(len(batch))

# Chunking documents into smaller chunks
def chunk_document(document: Document, tokens_per_chunk: int, stride: Optional[int] = None) -> list[Document]:

    if stride is None:
        stride = tokens_per_chunk

    tok = anthropic.Anthropic().get_tokenizer()

    raw_text = document.text
    tokenized_text = tok.encode(raw_text).ids

    chunks = []
    for i in range(0, len(tokenized_text), stride):
        chunk = tokenized_text[i:i + tokens_per_chunk]
        chunk_text = tok.decode(chunk)
        chunk_document = Document(text=chunk_text, metadata=document.metadata)
        chunks.append(chunk_document)
    return chunks


## Elasticsearch uploading
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

def upload_to_elasticsearch(
        input_file: str,
        index_name: str,
        cloud_id: str,
        api_key_id: str,
        api_key: str) -> None:
    
    # Load the documents
    documents: list[Document] = []
    file_type = input_file.split(".")[-1]
    if file_type == "jsonl":
        with open(input_file, "r") as f:
            for i, line in enumerate(f):
                data = json.loads(line)
                text = data["text"]
                if text is None:
                    raise ValueError(f"Invalid jsonl file. 'text' key is missing on line {i}")
                metadata = data.get("metadata", None)
                doc = Document(text=text, metadata=metadata)
                documents.append(doc)
    else:
        raise ValueError("Invalid file_type. Supported types: 'jsonl'")
    
    # Upload the documents

    ## Create the Elasticsearch client
    es = Elasticsearch(
        cloud_id=cloud_id,
        api_key=(api_key_id, api_key),
    )

    ## Upload the documents
    def docs_to_generator():
        for i, document in enumerate(documents):
            yield {
                "_index": index_name,
                "_id": i,
                "text": document.text,
                "metadata": document.metadata
            }
    
    bulk(es, docs_to_generator())
    es.indices.refresh(index=index_name)