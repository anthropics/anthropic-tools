# Claude Tool Use Examples
## Give Claude access to an API <a id="api-example"></a>
A very common use case for tools is to give Claude access to an API. Let's demonstrate this process by giving Claude access to a public weather API that fetches the weather for a given city.

To start, we will need to import the `requests` package, as well as `BaseTool` and `ToolUser`.
```python
import requests

from tool_use_package.base_tool import BaseTool
from tool_use_package.tool_user import ToolUser
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
messages = [{"role": "human", "content": "I live in San Francisco, what shold I wear today?"}]
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

messages = [{"role": "human", "content": "Who is our oldest employee?"}]
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

It's easy to create a new search tool to connect Claude to additional data sources. The provided `BaseSearchTool` class can simply be extended.

To demonstrate this process, let's take a look at how we extended `BaseSearchTool` to create a tool Claude can use to search over an Elasticsearch index.

To start, let's define our Elasticsearch search tool:

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
        # init and connect to elasticsearch instance
        
    def truncate_page_content(self, page_content: str) -> str:
        # [Code hidden for brevity]
        # setup tokenizer in order to truncate page_content

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
```

Creating a search tool for Elasticsearch was straightforward - we just extended the `BaseSearchTool` class and implemented the `raw_search()` and `process_raw_search_results()` methods. This allowed us to perform searches on an Elasticsearch index and translate the results into `BaseSearchResult` objects.

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

# Pass the Amazon search tool instance into ToolUser
tool_user = ToolUser([amazon_search_tool])
```

Finally, we pass our `amazon_search_tool` to `ToolUser` and run our query!
```python
tool_user = ToolUser([amazon_search_tool])

print(tool_user.use_tools("I want to get my daughter more interested in science. What kind of gifts should I get her?", single_function_call=False))
```