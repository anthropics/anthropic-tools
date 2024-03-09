# Import required external packages
import wikipedia
from anthropic import Anthropic
from dataclasses import dataclass

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from .base_search_tool import BaseSearchResult, BaseSearchTool

# Define our custom Wikipedia Search Tool by inheriting BaseSearchTool (which itself inhherits BaseTool) and defining its use_tool() method.
class WikipediaSearchTool(BaseSearchTool):
    def __init__(self,
                 name="search_wikipedia",
                 description="The search_wikipedia tool will exclusively search over Wikipedia for pages similar to your query. It returns for each page its title and the full page content. Use this tool to get up-to-date and comprehensive information on a topic. Queries made to this tool should be as atomic as possible. The tool provides broad topic keywords rather than niche search topics. For example, if the query is 'Can you tell me about Odysseus's journey in the Odyssey?' the search query you make should be 'Odyssey'. Here's another example: if the query is 'Who created the first neural network?', your first query should be 'neural network'. As you can see, these queries are quite short. Think generalized keywords, not phrases.",
                 parameters=[
                    {"name": "query", "type": "str", "description": "The search term to enter into the Wikipedia search engine. Remember to use broad topic keywords."},
                    {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is a Wikipedia page."}
                ],
                 truncate_to_n_tokens=5000):
        super().__init__(name, description, parameters)
        self.truncate_to_n_tokens = truncate_to_n_tokens
        if truncate_to_n_tokens is not None:
            self.tokenizer = Anthropic().get_tokenizer()
    
    def raw_search(self, query: str, n_search_results_to_use: int):
        print("Query: ", query)
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
            search_results.append(BaseSearchResult(content=self.truncate_page_content(page.content), source=page.url))
            print("Reading content from: ", page.url)
        
        return search_results
    
    def truncate_page_content(self, page_content: str):
        if self.truncate_to_n_tokens is None:
            return page_content.strip()
        else:
            return self.tokenizer.decode(self.tokenizer.encode(page_content).ids[:self.truncate_to_n_tokens]).strip()
        
if __name__ == "__main__":
    from ...tool_user import ToolUser
    tool_user = ToolUser([WikipediaSearchTool()])
    messages = [{"role":"user", "content":"Can you teach me about the Starship test flight?"}]
    print(tool_user.use_tools(messages=messages, execution_mode="automatic"))
