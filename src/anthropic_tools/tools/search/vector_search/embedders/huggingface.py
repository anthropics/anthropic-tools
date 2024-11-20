from tenacity import retry, wait_exponential, stop_after_attempt
import requests
import json

from .base_embedder import Embedding, BaseEmbedder

class HuggingFaceEmbedder(BaseEmbedder):

    def __init__(self, api_key: str, model_name: str):
        """
        :param api_key: A HuggingFace API key. Get one at https://huggingface.co/docs/api-inference/quicktour.
        :param model_name: The name of the embeddding model to use. 
        """
        self.api_key = api_key
        self.model_name = model_name

        self.url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        config_url = f'https://huggingface.co/{model_name}/resolve/main/config.json'
        response = requests.get(config_url)
        if response.status_code == 200:
            config = json.loads(response.text)
            embedding_dimension = config["hidden_size"]
        else:
            raise RuntimeError(
                f"Could not get config for model {model_name}"
            )

        self.dim = embedding_dimension

    def embed(self, text: str) -> Embedding:
        emb = self.embed_batch([text])
        return emb[0]
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10))
    def embed_batch(self, texts: list[str]) -> list[Embedding]:
        response = requests.post(
            self.url,
            headers=self.headers,
            json={"inputs": texts})
        result = response.json()
        embeddings = []
        if isinstance(result, list):
            embeddings = result
        elif list(result.keys())[0] == "error":
            raise RuntimeError(
                "The model is currently loading, please re-run the text."
            )
        return [Embedding(embedding=embedding, text=text) for embedding, text in zip(embeddings, texts)]