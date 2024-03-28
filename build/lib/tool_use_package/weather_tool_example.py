# This contains the code for our WeatherTool example. You can also read about it in the getting started section of the ReadMe.
# The goal here is to demonstrate how to extend the BaseTool class to make your own tool, and how to pass a tool into the ToolUser class and use that class to Give Claude the ability to use that tool.

# Let's say we want to ask Claude to help us get dressed each morning. An important part of that process is knowing what temperature you might face.
# Unfortunately, normal Claude doesn't have access to the day's weather forecast. The solution? A weather tool!

# Import needed external packages
import requests

# We start by importing the necessary classes, BaseTool for defining our weather tool, and ToolUser for using it with Claude.
from .tools.base_tool import BaseTool
from .tool_user import ToolUser


# In order to define our tool we inherit the BaseTool class.
# In many cases (like this one) we then simply need to define the use_tool() method, which is a python function that is executed when Claude decides to use the tool. BaseTool will handle the rest.
class WeatherTool(BaseTool):
    """Retrieves the weather """

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

# Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters 
tool_name = "get_weather"
tool_description = """The get_weather tool will return weather data for a given city, including temperature and wind speed."""
tool_parameters = [
    {"name": "city", "type": "str", "description": "The city for which you would like the weather."} 
]

weather_tool = WeatherTool(tool_name, tool_description, tool_parameters)

# Pass the tool instance into the ToolUser
tool_user = ToolUser([weather_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    messages = [{"role":"user", "content":"I live in San Francisco, what should I wear today?"}]
    print(tool_user.use_tools(messages, execution_mode="automatic"))
