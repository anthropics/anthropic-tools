import requests

from tool_use_package.tools.base_tool import BaseTool
from tool_use_package.tool_user import ToolUser

# 1. Define the Tool
class GetLatitudeAndLongitude(BaseTool):
    """Returns the latitude and longitude for a given place name."""
    
    def use_tool(self,place):
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': place, 'format': 'json', 'limit': 1}
        response = requests.get(url, params=params).json()
        if response:
            lat = response[0]["lat"]
            lon = response[0]["lon"]
            print(f"invoke lat and lon tools {place}, {lat},{lon}")
            return {"latitude": lat, "longitude": lon}
        else:
            return None
        
class GetWeatherTool(BaseTool):
    """Returns weather data for a given latitude and longitude."""

    def use_tool(self,latitude: str, longitude: str):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        response = requests.get(url)
        result = response.json()
        print(f"invoke getweather tools {latitude}, {longitude},{result}") 
        return result





# 2. Tool Description
getweather_tool_name = "perform_getweather"
getweather_tool_description = """Returns weather data for a given latitude and longitude.
Use this tool WHENEVER you need to perform any getweather calculation, as it will ensure your answer is precise."""
getweather_tool_parameters = [
    {"name": "latitude", "type": "str", "description": "latitude."},
    {"name": "longitude", "type": "str", "description": "longitude."}
]

getlat_and_lon_tool_name = "perform_getweather_tools"
getlat_and_lon_tool_description = """Returns the latitude and longitude for a given place name..
Use this tool WHENEVER you need to perform any getweather calculation, as it will ensure your answer is precise."""
getlat_and_lon_tool_parameters = [
    {"name": "place", "type": "str", "description": "place name."},
]

getweather_tool = GetWeatherTool(getweather_tool_name, getweather_tool_description, getweather_tool_parameters)
getlatitude_longitude_tool = GetLatitudeAndLongitude(getlat_and_lon_tool_name ,getlat_and_lon_tool_description,getlat_and_lon_tool_parameters)

# 3. Assign Tool and Ask Claude
tool_user = ToolUser([getlatitude_longitude_tool,getweather_tool],first_party=False , model="anthropic.claude-3-sonnet-20240229-v1:0")
messages = [
    {
        "role":"user", 
        "content":"""
            Can you check the weather for me in Paris, France?"""
    }
]
print(tool_user.use_tools(messages, execution_mode="automatic"))