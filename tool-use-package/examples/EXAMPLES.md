# Claude Tool Use Examples
## Give Claude access to an API <a id="api-example"></a>
One very common use case for Tools is to give Claude access to an API. Let's demonstrate this process by giving Claude access to a public weather API that fetches the weather for a given city.

To start, we will need to import the `requests` package, as well as `BaseTool` and `ToolUser`.
```python
import requests

from ..base_tool import BaseTool
from ..tool_user import ToolUser
```

We define our `WeatherTool`.  
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

You may also notice that we set `single_function_call=False`, this means that Claude will have the answers to its tool usage automatically fed back in until it decides it has done enough to answer your query, at which point it will respond to you with that answer. If you set `single_function_call=True`, Claude will stop after its first use of a tool and you will be returned the tool it used and the results of using that tool.
```python
# Pass the tool instance into the ToolUser
tool_user = ToolUser([weather_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
print(tool_user.use_tools("I live in San Francisco, what shold I wear today?", single_function_call=False))
```

## Let Claude search across a variety of data sources <a id="search-example"></a>
To be filled out by Alex.

## Let Claude call a SQL database <a id="sql-example"></a>
To be filled out  by Nick.