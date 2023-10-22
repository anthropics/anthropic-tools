from anthropic import Anthropic
from elasticsearch import Elasticsearch

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from .base_search_tool import BaseSearchResult, BaseSearchTool

# Elasticsearch Searcher Tool
class ElasticsearchSearchTool(BaseSearchTool):

    def __init__(self,
                name,
                description,
                parameters,
                elasticsearch_cloud_id,
                elasticsearch_api_key_id,
                elasticsearch_api_key,
                elasticsearch_index,
                truncate_to_n_tokens = 5000):
        """
        :param name: The name of the tool.
        :param description: The description of the tool.
        :param parameters: The parameters for the tool.
        :param elasticsearch_cloud_id: The cloud id for the Elasticsearch index.
        :param elasticsearch_api_key_id: The api key id for the Elasticsearch index.
        :param elasticsearch_api_key: The api key for the Elasticsearch index.
        :param elasticsearch_index: The index to search over.
        :param truncate_to_n_tokens: The number of tokens to truncate the page content to. If None, the full page content is returned.
        """
        super().__init__(name, description, parameters)

        self.index = elasticsearch_index
        self.cloud_id = elasticsearch_cloud_id
        self.api_key_id = elasticsearch_api_key_id
        self.api_key = elasticsearch_api_key
        self._connect_to_elasticsearch()

        self.truncate_to_n_tokens = truncate_to_n_tokens
        if truncate_to_n_tokens is not None:
            self.tokenizer = Anthropic().get_tokenizer() 
    
    def _connect_to_elasticsearch(self):
        self.client = Elasticsearch(
            cloud_id=self.cloud_id,
            api_key=(self.api_key_id, self.api_key)
        )
        if not self.client.indices.exists(index=self.index):
            raise ValueError(f"Elasticsearch Index {self.index} does not exist.")
        index_mapping = self.client.indices.get_mapping(index=self.index)
        if "text" not in index_mapping.body[self.index]["mappings"]["properties"].keys():
            raise ValueError(f"Index {self.index} does not have a field called 'text'.")
    
    def truncate_page_content(self, page_content: str) -> str:
        if self.truncate_to_n_tokens is None:
            return page_content.strip()
        else:
            return self.tokenizer.decode(self.tokenizer.encode(page_content).ids[:self.truncate_to_n_tokens]).strip()

    def raw_search(self, query: str, n_search_results_to_use: int) -> list[BaseSearchResult]:
        results = self.client.search(index=self.index,
                                     query={"match": {"text": query}})
        search_results: list[BaseSearchResult] = []
        for result in results["hits"]["hits"]:
            if len(search_results) >= n_search_results_to_use:
                break
            content = self.truncate_page_content(result["_source"]["text"])
            search_results.append(BaseSearchResult(source=str(hash(content)), content=content))

        return search_results