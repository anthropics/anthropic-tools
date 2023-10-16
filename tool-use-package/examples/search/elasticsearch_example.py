import os
from anthropic import Anthropic
from elasticsearch import Elasticsearch

# Import the requisite ToolUser class
from ...tool_user import ToolUser

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from .base_search_tool import BaseSearchResult, BaseSearchTool

import logging
logger = logging.getLogger(__name__)

# Elasticsearch Searcher
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
            content = result["_source"]["text"]
            search_results.append(BaseSearchResult(source=str(hash(content)), content=content))

        return search_results
    
    def process_raw_search_results(self, results: list[BaseSearchResult]) -> list[list[str]]:
        processed_search_results = [[result.source, self.truncate_page_content(result.content)] for result in results]
        return processed_search_results

# Upload Amazon product data to Elasticsearch
def upload_data():
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    api_key_id = os.getenv("ELASTICSEARCH_API_KEY_ID")
    api_key = os.getenv("ELASTICSEARCH_API_KEY")

    index_name = "amazon-products-database"

    if cloud_id is None or api_key_id is None or api_key is None:
        raise ValueError("ELASTICSEARCH_CLOUD_ID, ELASTICSEARCH_API_KEY_ID, and ELASTICSEARCH_API_KEY must be set as environment variables")

    es = Elasticsearch(
            cloud_id=cloud_id,
            api_key=(api_key_id, api_key),
        )
    
    if not es.indices.exists(index=index_name):
        from search.utils import upload_to_elasticsearch
        upload_to_elasticsearch(
            input_file="data/amazon-products.jsonl",
            index_name=index_name,
            cloud_id=cloud_id,
            api_key_id=api_key_id,
            api_key=api_key
        )

# Create a tool user that can use the Amazon search tool
def create_amazon_search_tool():
    # Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters 
    tool_name = "search_amazon"
    tool_description = """The search engine will search over the Amazon Product database, and return for each product its title, description, and a set of tags."""
    tool_parameters = [
        {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
        {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is an Amazon product."}
    ]

    amazon_search_tool = ElasticsearchSearchTool(tool_name, tool_description, tool_parameters, os.environ["ELASTICSEARCH_CLOUD_ID"], os.environ["ELASTICSEARCH_API_KEY_ID"], os.environ["ELASTICSEARCH_API_KEY"], "amazon-products-database")

    # Pass the tool instance into the ToolUser
    tool_user = ToolUser([amazon_search_tool])
    return tool_user

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    upload_data()
    tool_user = create_amazon_search_tool()
    print(tool_user.use_tools("I want to get my daughter more interested in science. What kind of gifts should I get her?", verbose=True, single_function_call=False))