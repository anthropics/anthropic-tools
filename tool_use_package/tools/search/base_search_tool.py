from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..base_tool import BaseTool

@dataclass
class BaseSearchResult:
    """
    A single search result.
    """

    content: str
    source: str

class BaseSearchTool(BaseTool):
    """A search tool that can run a query and return a formatted string of search results."""

    @abstractmethod
    def raw_search(self, query: str, n_search_results_to_use: int):
        """
        Runs a query using the searcher, then returns the raw search results without formatting.

        :param query: The query to run.
        :param n_search_results_to_use: The number of results to return.
        """
    
    @abstractmethod
    def process_raw_search_results(self, results: list[BaseSearchResult]):
        """
        Extracts the raw search content from the search results and returns a list of strings that can be passed to Claude.

        :param results: The search results to extract.
        """
    
    def use_tool(self, query: str, n_search_results_to_use: int):
        raw_search_results = self.raw_search(query, n_search_results_to_use)
        processed_search_results = self.process_raw_search_results(raw_search_results)
        displayable_search_results = BaseSearchTool._format_results_full(processed_search_results)
        return displayable_search_results
    
    @staticmethod
    def _format_results(extracted: list[list[str]]):
        """
        Joins and formats the extracted search results as a string.

        :param extracted: The extracted search results to format.
        """

        result = "\n".join(
            [
                f'<item index="{i+1}">\n<source>{r[0]}</source>\n<page_content>\n{r[1]}\n</page_content>\n</item>'
                for i, r in enumerate(extracted)
            ]
        )
        return result
         
    @staticmethod
    def _format_results_full(extracted: list[list[str]]):
        """
        Formats the extracted search results as a string, including the <search_results> tags.
        
        :param extracted: The extracted search results to format.
        """
        
        return f"\n<search_results>\n{BaseSearchTool._format_results(extracted)}\n</search_results>"