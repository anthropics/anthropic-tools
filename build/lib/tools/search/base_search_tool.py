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
    
    def use_tool(self, query: str, n_search_results_to_use: int):
        raw_search_results = self.raw_search(query, n_search_results_to_use)
        displayable_search_results = BaseSearchTool._format_results_full(raw_search_results)
        return displayable_search_results
    
    @staticmethod
    def _format_results(raw_search_results:list[BaseSearchResult]):
        """
        Joins and formats the extracted search results as a string.

        :param extracted: The extracted search results to format.
        """

        result = "\n".join(
            [
                f'<item index="{i+1}">\n<source>{r.source}</source>\n<page_content>\n{r.content}\n</page_content>\n</item>'
                for i, r in enumerate(raw_search_results)
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