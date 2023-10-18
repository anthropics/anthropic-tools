import os
from typing import Optional
from anthropic import Anthropic
import requests
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt
from bs4 import BeautifulSoup
import aiohttp

# Import the requisite ToolUser class
from ...tool_user import ToolUser

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from .base_search_tool import BaseSearchResult, BaseSearchTool

import logging
logger = logging.getLogger(__name__)

# Brave Searcher
class BraveAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10))
    def search(self, query: str) -> dict:
        headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query,
                    "count": 20 # Max number of results to return, can filter down later
                    },
            headers=headers,
            timeout=60
        )
        if resp.status_code != 200:
            logger.error(f"Search request failed: {resp.text}")
            return {}
        return resp.json()

class BraveSearchTool(BaseSearchTool):

    def __init__(self, name, description, parameters, brave_api_key, truncate_to_n_tokens=5000):
        """
        :param name: The name of the tool.
        :param description: The description of the tool.
        :param parameters: The parameters for the tool.
        :param brave_api_key: The Brave API key to use for searching. Get one at https://api.search.brave.com/register.
        :param truncate_to_n_tokens: The number of tokens to truncate web page content to.
        """
        super().__init__(name, description, parameters)
        self.api = BraveAPI(brave_api_key)
        self.truncate_to_n_tokens = truncate_to_n_tokens
        if truncate_to_n_tokens is not None:
            self.tokenizer = Anthropic().get_tokenizer()

    def parse_faq(self, faq: dict) -> BaseSearchResult:
        """
        https://api.search.brave.com/app/documentation/responses#FAQ
        """
        snippet = (
            f"FAQ Title: {faq.get('title', 'Unknown')}"
            f"Question: {faq.get('question', 'Unknown')}"
            f"Answer: {faq.get('answer', 'Unknown')}"
        )
        
        return BaseSearchResult(
            source=faq.get("url", ""),
            content=snippet
        )
    
    def parse_news(self, news_item: dict) -> Optional[BaseSearchResult]:
        """
        https://api.search.brave.com/app/documentation/responses#News
        """
        article_description: str = news_item.get("description", "")

        # Throw out items where the description is tiny or doesn't exist.
        if len(article_description) < 5:
            return None

        snippet = (
            f"News Article Title: {news_item.get('title', 'Unknown')}"
            f"News Article Description: {article_description}"
            f"News Article Age: {news_item.get('age', 'Unknown')}"
            f"News Article Source: {news_item.get('meta_url', {}).get('hostname', 'Unknown')}"
        )
        
        return BaseSearchResult(
            source=news_item.get("url", ""),
            content=snippet
        )

    @staticmethod
    def remove_strong(web_description: str):
        # this is for cleaning up the brave web descriptions
        return (
            web_description.replace("<strong>", "")
            .replace("</strong>", "")
            .replace("&#x27;", "'")
        )
    
    async def parse_web(self, web_item: dict, query: str) -> BaseSearchResult:
        """
        https://api.search.brave.com/app/documentation/responses#Search
        """
        url = web_item.get("url", "")
        title = web_item.get("title", "")
        description = self.remove_strong(web_item.get("description", ""))
        snippet = (
            f"Web Page Title: {title}"
            f"Web Page URL: {url}"
            f"Web Page Description: {description}"
        )

        try:
            content = await self.__get_url_content(url)
            if not content:
                return BaseSearchResult(
            source=url,
            content=""
            )
            snippet+="\nWeb Page Content: " + self.truncate_page_content(content)
        except:
            logger.warning(f"Failed to scrape {url}")
        return BaseSearchResult(
            source=url,
            content=snippet
        )

    def truncate_page_content(self, page_content: str):
        if self.truncate_to_n_tokens is None:
            return page_content.strip()
        else:
            return self.tokenizer.decode(self.tokenizer.encode(page_content).ids[:self.truncate_to_n_tokens]).strip()

    def raw_search(self, query: str, n_search_results_to_use: int) -> list[BaseSearchResult]:
        """
        Run a search using the BraveAPI and return search results. Here are some details on the Brave API:

        Each search call to the Brave API returns the following fields:
         - faq: Frequently asked questions that are relevant to the search query (only on paid Brave tier).
         - news: News results relevant to the query.
         - web: Web search results relevant to the query.
         - [Thrown Out] videos: Videos relevant to the query.
         - [Thrown Out] locations: Places of interest (POIs) relevant to location sensitive queries.
         - [Thrown Out] infobox: Aggregated information on an entity showable as an infobox.
         - [Thrown Out] discussions: Discussions clusters aggregated from forum posts that are relevant to the query.

        There is also a `mixed` key, which tells us the ranking of the search results.

        We may throw some of these back in, in the future. But we're just going to document the behavior here for now.
        """
        
        # Run the search
        search_response = self.api.search(query)
        print("Query: ", query)
        print("Searching...")
        # Order everything properly
        correct_ordering = search_response.get("mixed", {}).get("main", [])

        # Extract the results
        faq_items = search_response.get("faq", {}).get("results", [])
        news_items = search_response.get("news", {}).get("results", [])
        web_items = search_response.get("web", {}).get("results", [])

        # Get the search results
        search_results: list[BaseSearchResult] = []
        async_web_parser_loop = asyncio.get_event_loop()
        web_parsing_tasks = [] # We'll queue up the web parsing tasks here, since they're costly

        for item in correct_ordering:
            item_type = item.get("type")
            if item_type == "web":
                web_item = web_items.pop(0)
                ## We'll add a placeholder search result here, and then replace it with the parsed web result later
                url = web_item.get("url", "")
                placeholder_search_result = BaseSearchResult(
                    source=url,
                    content=f"Web Page Title: {web_item.get('title', '')}\nWeb Page URL: {url}\nWeb Page Description: {self.remove_strong(web_item.get('description', ''))}"
                )
                search_results.append(placeholder_search_result)
                ## Queue up the web parsing task
                task = async_web_parser_loop.create_task(self.parse_web(web_item, query))
                web_parsing_tasks.append(task)
            elif item_type == "news":
                parsed_news = self.parse_news(news_items.pop(0))
                if parsed_news is not None:
                    search_results.append(parsed_news)
            elif item_type == "faq":
                parsed_faq = self.parse_faq(faq_items.pop(0))
                search_results.append(parsed_faq)
            if len(search_results) >= n_search_results_to_use:
                break

        ## Replace the placeholder search results with the parsed web results
        web_results = async_web_parser_loop.run_until_complete(asyncio.gather(*web_parsing_tasks))
        web_results_urls = [web_result.source for web_result in web_results]
        for i, search_result in enumerate(search_results):
            url = search_result.source
            if url in web_results_urls:
                search_results[i] = web_results[web_results_urls.index(url)]
                print("Reading content from: ", url)

        return search_results
    
    def process_raw_search_results(self, results: list[BaseSearchResult]) -> list[list[str]]:
        # We don't need to do any processing here, since we already formatted the results in the `parse` functions.
        processed_search_results = [[result.source, result.content.strip()] for result in results]
        return processed_search_results

    async def __get_url_content(self, url: str) -> Optional[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text(strip=True, separator='\n')
                    return text
        return None
    

# Initialize an instance of the tool by passing in tool_name, tool_description, tool_parameters, and your Brave API key (make sure to set BRAVE_API_KEY as an env variable).
tool_name = "search_brave"
tool_description = """The search engine will search using the Brave search engine for web pages similar to your query. It returns for each page its url and the full page content. Use this tool if you want to make web searches about a topic."""
tool_parameters = [
    {"name": "query", "type": "str", "description": "The search query to enter into the Brave search engine. "},
    {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is a website page."}
]

brave_search_tool = BraveSearchTool(tool_name, tool_description, tool_parameters, os.environ['BRAVE_API_KEY'])

# Pass the Brave tool instance into the ToolUser
tool_user = ToolUser([brave_search_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    print("\n------------Answer------------", tool_user.use_tools("Who scored the most goals in the 2023 Women's World Cup?", verbose=False, single_function_call=False))