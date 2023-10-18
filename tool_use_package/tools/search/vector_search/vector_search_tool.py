import os

# Import the requisite ToolUser class
from ....tool_user import ToolUser

# Import the embedder we will use for our search tool
from .embedders.huggingface import HuggingFaceEmbedder
from .constants import DEFAULT_EMBEDDER, DATA_FILE

# Import our base search tool from which all other search tools inherit. We use this pattern to make building new search tools easy.
from ..base_search_tool import BaseSearchResult, BaseSearchTool

# Vector DB Searcher
class VectorSearchTool(BaseSearchTool):

    def __init__(self,
                  name,
                  description,
                  parameters,
                  vector_store,
                  embedder = None):
        """
        :param name: The name of the tool.
        :param description: The description of the tool.
        :param parameters: The parameters for the tool.
        :param vector_store: The vector store to use for searching.
        :param embedder: The name of the embedder model to use. Defaults to a HuggingFace embedder with the model "sentence-transformers/paraphrase-MiniLM-L6-v2".
        """
        super().__init__(name, description, parameters)

        if embedder is None:
            # Get your HuggingFace API key from https://huggingface.co/docs/api-inference/quicktour
            embedder = HuggingFaceEmbedder(os.environ["HUGGINGFACE_API_KEY"], DEFAULT_EMBEDDER)
            print("here")
        self.embedder = embedder
        self.vector_store = vector_store

    def raw_search(self, query: str, n_search_results_to_use: int) -> list[BaseSearchResult]:
        print("Query: ", query)
        print("Searching...")
        query_embedding = self.embedder.embed(query)
        search_results = self.vector_store.query(query_embedding, n_search_results_to_use=n_search_results_to_use)
        return search_results
    
    def process_raw_search_results(self, results: list[BaseSearchResult]) -> list[list[str]]:
        processed_search_results = [[result.source, result.content.strip()] for result in results]
        print("------------Results------------")
        for i, item in enumerate(processed_search_results):
            print(f"------------Result {i+1}------------")
            print(item[1] + "\n")
        return processed_search_results


# Upload Amazon product data to Pinecone
def upload_data():

    # Import the vector store we will use for our search tool
    import pinecone
    from ....examples.search.vectorstores.pinecone import PineconeVectorStore
    from ....utils import embed_and_upload

    # Initialize Pinecone and create a vector store. Get your Pinecone API key from https://www.pinecone.io/start/
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_ENVIRONMENT = os.environ["PINECONE_ENVIRONMENT"]
    PINECONE_DATABASE = os.environ["PINECONE_DATABASE"]

    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    if PINECONE_DATABASE not in pinecone.list_indexes():
        print("No remote vectorstore found.")

        batch_size = 128
        input_file = DATA_FILE
        print("Creating new index and filling it from local text files. This may take a while...")
        pinecone.create_index(PINECONE_DATABASE, dimension=768, metric="cosine")
        vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
        embed_and_upload(input_file, vector_store, batch_size=batch_size)
    else:
        vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
    return vector_store

# Create a tool user that can use the Amazon search tool
def create_amazon_search_tool(vector_store):
    # Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters 
    tool_name = "search_amazon"
    tool_description = """The search engine will search over the Amazon Product database, and return for each product its title, description, and a set of tags."""
    tool_parameters = [
        {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
        {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is an Amazon product."}
    ]

    amazon_search_tool = VectorSearchTool(tool_name, tool_description, tool_parameters, vector_store)

    # Pass the tool instance into the ToolUser
    tool_user = ToolUser([amazon_search_tool])
    return tool_user

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    vector_store = upload_data()
    tool_user = create_amazon_search_tool(vector_store)
    print("\n------------Answer------------", tool_user.use_tools("I want to get my daughter more interested in science. What kind of gifts should I get her?", verbose=False, single_function_call=False))