# Import required external packages
import wikipedia
from anthropic import Anthropic
from dataclasses import dataclass

# Import the requisite ToolUser class
from ...tool_user import ToolUser

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from .base_search_tool import BaseSearchResult, BaseSearchTool

# Define a dataclass to help us keep our Wikipedia search results in standard format
@dataclass
class WikipediaSearchResult(BaseSearchResult):
    title: str

# Define our custom Wikipedia Search Tool by inheriting BaseSearchTool (which itself inhherits BaseTool) and defining its use_tool() method.
class WikipediaSearchTool(BaseSearchTool):
    def __init__(self, name, description, parameters, truncate_to_n_tokens=5000):
        super().__init__(name, description, parameters)
        self.truncate_to_n_tokens = truncate_to_n_tokens
        if truncate_to_n_tokens is not None:
            self.tokenizer = Anthropic().get_tokenizer()
    
    def raw_search(self, query: str, n_search_results_to_use: int):
        return self._search(query, n_search_results_to_use)
    
    def process_raw_search_results(self, results: list[WikipediaSearchResult]):
        return [[result.source, f'Page Title: {result.title.strip()}\nPage Content:\n{self.truncate_page_content(result.content)}'] for result in results]
    
    def truncate_page_content(self, page_content: str):
        if self.truncate_to_n_tokens is None:
            return page_content.strip()
        else:
            return self.tokenizer.decode(self.tokenizer.encode(page_content).ids[:self.truncate_to_n_tokens]).strip()
    
    def _search(self, query: str, n_search_results_to_use: int):
        results = wikipedia.search(query)
        search_results = []

        for result in results:
            if len(search_results) >= n_search_results_to_use:
                break
            try:
                page = wikipedia.page(result)
            except:
                # the Wikipedia API is a little flaky, so we just skip over pages that fail to load
                continue
            search_results.append(WikipediaSearchResult(content=page.content, title=page.title, source=page.url))
        
        return search_results

# Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters 
tool_name = "search_wikipedia"
tool_description = """The search_wikipedia tool will exclusively search over Wikipedia for pages similar to your query. It returns for each page its title and the full page content. Use this tool to get up-to-date and comprehensive information on a topic. Queries made to this tool should be as atomic as possible. The tool provides broad topic keywords rather than niche search topics. For example, if the query is "Can you tell me about Odysseus's journey in the Odyssey?" the search query you make should be "Odyssey". Here's another example: if the query is "Who created the first neural network?", your first query should be "neural network". As you can see, these queries are quite short. Think generalized keywords, not phrases."""
tool_parameters = [
    {"name": "query", "type": "str", "description": "The search term to enter into the Wikipedia search engine. Remember to use broad topic keywords."},
    {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is a Wikipedia page."}
]

wikipedia_search_tool = WikipediaSearchTool(tool_name, tool_description, tool_parameters)

# Pass the tool instance into the ToolUser
tool_user = ToolUser([wikipedia_search_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    print(tool_user.use_tools("What's the name of the latest material that was claimed to be a room temperature superconductor?", verbose = True))