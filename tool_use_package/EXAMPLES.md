# Claude Tool Use Examples
## Give Claude access to an API <a id="api-example"></a>
A very common use case for tools is to give Claude access to an API. Let's demonstrate this process by giving Claude access to a public weather API that fetches the weather for a given city.

To start, we will need to import the `requests` package, as well as [`BaseTool`](tools/base_tool.py) and [`ToolUser`](tool_user.py).
```python
import requests

from .tool_use_package.tools.base_tool import BaseTool
from .tool_use_package.tool_user import ToolUser
```

Define our `WeatherTool`.  
To give Claude access to an API endpoint, we simply make the `use_tool()` method a call to the relevant endpoint.
```python
class WeatherTool(BaseTool):
    """Retrieves the weather for a given city."""

    def use_tool(self, city: str):
        """Gets the lat and long of the given city, then uses these to get the weater forecast from the public open-meteo API."""

        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': city, 'format': 'json', 'limit': 1}
        response = requests.get(url, params=params).json()
        
        if response:
            lat = response[0]["lat"]
            lon = response[0]["lon"]
        else:
            raise ValueError("Could not find lat and long coordinates for given place.")
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url)
        response_json = response.json()

        clean_json = {"current_weather_units": response_json['current_weather_units'], "current_weather": response_json['current_weather']}

        return clean_json
```

Once we have `WeatherTool` defined, we instantiate it by passing in `name`, `description`, and `parameters` for the tool.
```python
tool_name = "get_weather"
tool_description = """The get_weather tool will return weather data for a given city, including temperature and wind speed."""
tool_parameters = [
    {"name": "city", "type": "str", "description": "The city for which you would like the weather."} 
]

weather_tool = WeatherTool(tool_name, tool_description, tool_parameters)
```

Finally, we create an instance of ToolUser, passing it a list containg our `weather_tool` instance.  
We then call tool_user.use_tools() with our query to let claude answer our question while making use of our provided tools where appropriate.
```python
# Pass the tool instance into the ToolUser
tool_user = ToolUser([weather_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
messages = [{"role": "user", "content": "I live in San Francisco, what shold I wear today?"}]
print(tool_user.use_tools(messages, execution_mode='automatic'))
```
You may also notice that we set `execution_mode='automatic'`, recall that this means Claude will have its tool usage requests automatically executed and fed back in until it decides it has done enough to answer your query, at which point it will respond to you with that answer. If you set `execution_mode='manual'`, Claude will stop after its first request to use a tool/tools and you will be returned the requested tool(s) to use and the arguments to use them with.

## Let Claude call a SQL database <a id="sql-example"></a>
One of the most powerful tools you can give Claude is the ability to query a database. Let's go over how we might use a tool to do just that, letting Claude query a SQLite DB.

We will need to import the `sqlite3` package, since we are going to work with a SQLite database. You will need to adjust this for your database type (such as psycopg2 for Postgres). We also import `BaseTool` and `ToolUser`. Lastly, we are going to use a special tool formatter for this tool, so we import it from prompt_constructors as well.
```python
import sqlite3 # Adjust for your DB type

from tool_use_package.base_tool import BaseTool
from tool_use_package.tool_user import ToolUser
from tool_use_package.prompt_constructors import construct_format_sql_tool_for_claude_prompt # Special fromatting that we want to define for SQL tools, will discuss more later
```

The below code should look pretty familiar to you by now (defining `SQLTool` by inheriting `BaseTool` and defininng its `use_tool()`method), with two exceptions.  
1. We have overridden the `__init__()` method so that the tool can also have attributes `db_schema` (the DB's schema), `db_conn` (a valid DB connection string), and `db_dialect` (the SQL dialect of the DB). We need to ensure that we also call `super().__init__(name, description, parameters)` to keep the core functionality of our tool working when we override `__init__()`.  
2. We have defined a `format_tool_for_claude()` method that is overriding the `format_tool_for_claude()` in `BaseTool`. This is a common technique we can use when we want to augment the part of the system prompt that describes how to use our tool to Claude. You should consider doing this if there are special features of your tool or information about it not easily addressed in standard format. In this case, that is information about the schema of the databse and the dialect. If you want to see these queries and how we are changing them you can check out `base_tool.py` and `prompt_constructors.py`.
```python
class SQLTool(BaseTool):
    """A tool that can run SQL queries against a datbase. db_conn should be a connection string such as sqlite3.connect('test.db')"""

    def __init__(self, name, description, parameters, db_schema, db_conn, db_dialect):
        super().__init__(name, description, parameters)
        self.db_schema = db_schema
        self.db_conn = db_conn
        self.db_dialect = db_dialect

    
    def use_tool(self, sql_query):
        """Executes a query against the given database connection."""
       
        cursor = self.db_conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        cursor.close()

        return results
    
    def format_tool_for_claude(self):
        """Overriding the base class format_tool_for_claude in this case, which we don't always do. Returns a formatted representation of the tool suitable for the Claude system prompt."""
        
        return construct_format_sql_tool_for_claude_prompt(self.name, self.description, self.parameters, self.db_schema, self.db_dialect)
```

In order to run the example and see Claude in action, you will need a SQL databse. Here is how you can easily make one for the purpose of this example.
```python
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('''
              CREATE TABLE employee_data (
              id INTEGER PRIMARY KEY, 
              name TEXT NOT NULL,
              age INTEGER NOT NULL
              )
              ''')  

cursor.execute("INSERT INTO employee_data VALUES (1, 'John', 42)")
cursor.execute("INSERT INTO employee_data VALUES (2, 'Jane', 36)")
conn.commit()
conn.close()
```

Now that we have our database, we can instantiate a SQLTool to work with it. Note how we specify the `db_schema` and `db_conn`.
```python
tool_name = "execute_sqlite3_query"
tool_description = """The execute_sqlite3_query tool will execute a given sql query against a sql database with the provided schema and return to you the results of that query."""
tool_parameters = tool_parameters = [{"name": "sql_query", "type": "str", "description": "The query to run."}]
tool_db_schema = """CREATE TABLE employee_data (
          id INTEGER PRIMARY KEY, 
          name TEXT NOT NULL,
          age INTEGER NOT NULL
          )"""
tool_db_conn = sqlite3.connect('test.db')
tool_db_dialect = 'SQLite'

sql_tool = SQLTool(tool_name, tool_description, tool_parameters, tool_db_schema, tool_db_conn, tool_db_dialect)
```

Finally, we pass `sql_tool` to `ToolUser` and run our query!
```python
tool_user = ToolUser([sql_tool])

messages = [{"role": "user", "content": "Who is our oldest employee?"}]
print(tool_user.use_tools(messages, single_function_call=False))
```
When you are done you can either manually delete the test.db file or run `os.remove('test.db')` to get rid of the temporary database we created.

## Let Claude search across a variety of data sources <a id="search-example"></a>
With Tools, Claude can now perform searches across different data sources to find and incorporate relevant information into its responses. This retrieval-augmented generation (RAG) allows Claude to access knowledge beyond its training data.

We've provided examples connecting Claude to four data sources:
- Vector database
- Elasticsearch index
- Wikipedia
- The open web

It's easy to create a new search tool to connect Claude to additional data sources. The provided [`BaseSearchTool`](tools/search/base_search_tool.py) class can simply be extended.

To demonstrate this process, let's take a look at how we extended `BaseSearchTool` to create a tool Claude can use to search over an Elasticsearch index.

To start,  we will need to import the [`BaseTool`](tools/base_tool.py) and [`ToolUser`](tool_user.py) classes.
```python
from .tool_use_package.tools.base_tool import BaseTool
from .tool_use_package.tool_user import ToolUser
```

Then, let's define our [`ElasticsearchSearchTool`](tools/search/elasticsearch_search_tool.py):

```python
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
        # [Code hidden for brevity]
        # init and connect to elasticsearch index
        
    def truncate_page_content(self, page_content: str) -> str:
        # [Code hidden for brevity]
        # setup tokenizer in order to truncate page_content

    def raw_search(self, query: str, n_search_results_to_use: int) -> list[BaseSearchResult]:
        # Search our elasticsearch index for our query
        results = self.client.search(index=self.index,
                                     query={"match": {"text": query}})

        # Iterate through the search results and format them into our BaseSearchResult class                            
        search_results: list[BaseSearchResult] = []
        for result in results["hits"]["hits"]:
            if len(search_results) >= n_search_results_to_use:
                break
            content = self.truncate_page_content(result["_source"]["text"])
            search_results.append(BaseSearchResult(source=str(hash(content)), content=content))

        return search_results
```

Creating a search tool for Elasticsearch was straightforward - we just extended the `BaseSearchTool` class and implemented the `raw_search()` method. This allowed us to perform searches on an Elasticsearch index and translate the results into a list of `BaseSearchResult` objects.

Now that we have created our tool, let's use it! We will follow a similar process as before with the other tools.

We start by defining the name, description, and parameters for our tool. In this example, we pre-loaded our elasticsearch index with Amazon product data so we will want to define our tool as such:
```python
tool_name = "search_amazon"
tool_description = """The search engine will search over the Amazon Product database, and return for each product its title, description, and a set of tags."""
tool_parameters = [
    {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
    {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is an Amazon product."}
]
```

Once we have our tool definitions, we can create the tool and pass in our elasticsearch credentials (defined as enviroment variables) and the name of our index.

```python
amazon_search_tool = ElasticsearchSearchTool(
    name=tool_name, 
    description=tool_description,
    parameters=tool_parameters, 
    elasticsearch_cloud_id=os.environ["ELASTICSEARCH_CLOUD_ID"],
    elasticsearch_api_key_id=os.environ["ELASTICSEARCH_API_KEY_ID"],
    elasticsearch_api_key=os.environ["ELASTICSEARCH_API_KEY"],
    elasticsearch_index="amazon-products-database")
```

Finally, we pass our `amazon_search_tool` to `ToolUser`, define our message, and call `use_tools`!
```python
tool_user = ToolUser([amazon_search_tool])

messages = [{"role":"user", "content":"I want to get my daughter more interested in science. What kind of gifts should I get her?"}]

print(tool_user.use_tools(messages, execution_mode="automatic"))
```

## Let Claude search over a vector database

We have provided a [`vector_search_tool`](tools/search/vector_search/vector_search_tool.py) that Claude can use to perform searches over vector databases. The tool works the same as the other search tools but with one caveat - you must define a vector store for the tool to use by extending the [`BaseVectorStore`](tools/search/vector_search/vectorstores/base_vector_store.py) class. Let's run through an example of how this works:

For demonstration purposes, we will be using [pinecone.io](https://www.pinecone.io) as our vector database. To start, we create the class [`PineconeVectorStore`](tools/search/vector_search/vectorstores/pinecone.py) by extending `upsert` and `query` methods in the `BaseVectorStore` class.

```python
class PineconeVectorStore(BaseVectorStore):
    def __init__(self, api_key: str, environment: str, index: str):
        self.api_key = api_key
        self.environment = environment
        self.index = index
        self.pinecone_index = self._init_pinecone_index()
        self.pinecone_index_dimensions = self.pinecone_index.describe_index_stats().dimension

    def _init_pinecone_index(self):
        # [Code hidden for brevity]
        # init and connect to pinecone index

    def query(self, query_embedding: Embedding, n_search_results_to_use: int = 10) -> list[BaseSearchResult]:
        if len(query_embedding.embedding) != self.pinecone_index_dimensions:
            raise ValueError(f"Query embedding dimension {len(query_embedding.embedding)} does not match Pinecone index dimension {self.pinecone_index_dimensions}")
        results = self.pinecone_index.query(
            vector=query_embedding.embedding, top_k=n_search_results_to_use, include_metadata=True
        )
        results=[BaseSearchResult(source=str(hash(match['metadata']['text'])), content=match['metadata']['text']) for match in results.matches]
        return results

    def upsert(self, embeddings: list[Embedding], upsert_batch_size: int = 128) -> None:
        embedding_chunks = chunked(embeddings, n=upsert_batch_size) # split embeddings into chunks of size upsert_batch_size
        current_index_size = self.pinecone_index.describe_index_stats()['total_vector_count'] # get the current index size from Pinecone
        i = 0 # keep track of the current index in the current batch
        for emb_chunk in embedding_chunks:
            # for each chunk of size upsert_batch_size, create a list of ids, vectors, and metadatas, and upsert them into the Pinecone index
            ids = [str(current_index_size+1+i) for i in range(i,i+len(emb_chunk))]
            vectors = [emb.embedding for emb in emb_chunk]
            metadatas = [{'text': emb.text} for emb in emb_chunk]
            records = list(zip(ids, vectors, metadatas))
            self.pinecone_index.upsert(vectors=records)
            i += len(emb_chunk) 
```

There's a few things going on in this class:

- In `init`, the Pinecone index is loaded (this assumes that the Pinecone index already exists).
- In `upsert`, we upsert the embeddings into the Pinecone index in batches of size `upsert_batch_size`. 
  - The embeddings are stored as a list of ids, vectors, and metadatas. The ids are the index of the embedding in the Pinecone index. Metadatas are used to store the text data for each embedding as Pinecone indices do not store text data by default.
- In `query`, the query embedding is compared to all embeddings in the Pinecone index using the similarity specified when the index was created.

Note that the vectorstore does not contain any logic for creating embeddings. It is assumed that the embeddings are created elsewhere using Embedders (we have provided a [HuggingFace Embedder](tools/search/vector_search/embedders/huggingface.py)) and passed to the vectorstore for storage and retrieval. The [utils.embed_and_upload()](tools/search/vector_search/utils.py) is a wrapper to help do this. 

In order to use the Embedder, please set your HuggingFace API key as an enviroment variable (get a key [here](https://huggingface.co/docs/api-inference/quicktour)):
```bash
# MacOS
export HUGGINGFACE_API_KEY={your_huggingface_api_key}
```

Let's use see how we can use the `utils.embed_and_upload()` method to embed Amazon product data and upload it to our Pinecone index.

```python
# Import pinecone and the vector store we created
import pinecone
from .tool_use_package.tools.search.vector_search.vectorstores.pinecone import PineconeVectorStore
from .tool_use_package.tools.search.vector_search.utils import embed_and_upload

# Initialize Pinecone and create a vector store. Get your Pinecone API key from https://www.pinecone.io/start/
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_ENVIRONMENT = os.environ["PINECONE_ENVIRONMENT"]
PINECONE_DATABASE = os.environ["PINECONE_DATABASE"]

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Upload data to index if index doesn't already exist
if PINECONE_DATABASE not in pinecone.list_indexes():
    batch_size = 128
    input_file = DATA_FILE_PATH

    # Create a new index and fill it with data from local text file. This may take a while...
    pinecone.create_index(PINECONE_DATABASE, dimension=768, metric="cosine")
    vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
    embed_and_upload(input_file, vector_store, batch_size=batch_size)
else:
    vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT, index=PINECONE_DATABASE)
```

Once we have our vectorstore set up with the index we want to use, we can now instantiate our [vector_search_tool](tools/search/vector_search/vector_search_tool.py).
```python
# Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters 
tool_name = "search_amazon"
tool_description = """The search engine will search over the Amazon Product database, and return for each product its title, description, and a set of tags."""
tool_parameters = [
    {"name": "query", "type": "str", "description": "The search term to enter into the Amazon search engine. Remember to use broad topic keywords."},
    {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is an Amazon product."}
]

amazon_search_tool = VectorSearchTool(tool_name, tool_description, tool_parameters, vector_store)
```

Finally, we pass our `amazon_search_tool` to `ToolUser`, define our message, and call `use_tools`!
```python
tool_user = ToolUser([amazon_search_tool])

messages = [{"role":"user", "content":"I want to get my daughter more interested in science. What kind of gifts should I get her?"}]

print(tool_user.use_tools(messages, execution_mode="automatic"))
```