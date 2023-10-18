# anthropic-tools

A repo for using tools/function calling with Anthropic models.

## Setup

Set your Anthropic API key as an environment variable:  
```bash
# MacOS
export ANTHROPIC_API_KEY={your_anthropic_api_key}
```

Create a Python Virtual Environment:  
```bash
# MacOS
python3 -m venv anthropictools
source anthropictools/bin/activate
```

Install Requirements:
```bash
pip install -r requirements.txt
```

## Getting Started
anthropic-tools follows a very simple architecture that lets users define and use tools with Claude. There are two classes users should be familiar with. If you know these two classes you can do anything.

Additionally, anthropic-tools supports a number of pre-built tools out of the box, built on top of the same primitives available to you. These are here in case you want even easier tool use for some of our most common tools, such as search or SQL.

### BaseTool
BaseTool is the class that should be used to define individual tools. All you need to do to create a tool is inherit `BaseTool` and define the `use_tool()` method.
```python
import datetime
from ..base_tool import BaseTool

class TimeOfDayTool(BaseTool):
    """Tool to get the current time of day."""
    def use_tool(self, time_zone):
        # Get the current time
        now = datetime.datetime.now()

        # Convert to the specified time zone
        tz = zoneinfo.ZoneInfo(time_zone)
        localized_time = now.astimezone(tz)

        return localized_time.strftime("%H:%M:%S")
```

Then, you simply instantiate your custom tool with `tool_name`, `tool_description`, and `tool_parameters`. Pay attention to the formatting of each.
```python
tool_name = "get_time_of_day"
tool_description = "Retrieve the current time of day in Hour-Minute-Second format for a specified time zone. Time zones should be written in standard formats such as UTC, US/Pacific, Europe/London."
tool_parameters = [
    {"name": "time_zone", "type": "str", "description": "The time zone to get the current time for, such as UTC, US/Pacific, Europe/London."}
]

time_of_day_tool = TimeOfDayTool(tool_name, tool_description, tool_parameters)
```
### ToolUser
ToolUser is passed a list of tools (child classes of BaseTool) and allows you to use Claude with those tools. To create a ToolUser instance simply pass it a list of one or more tools.
```python
from ..tool_user import ToolUser
time_tool_user = ToolUser([time_of_day_tool])
```

You can then make use of your ToolUser by calling its `use_tools()` method and passing in your desired prompt.
```python
time_tool_user.use_tools("What time is it in Los Angeles?")
```

### Putting it Together
Putting concepts one and two together above, a full implementation with multiple tools might look something like this:
```python
import datetime
from ..base_tool import BaseTool
from ..tool_user import ToolUser

# Create Tools
class AdditionTool(BaseTool):
    """Tool to add two numbers together."""
    def use_tool(self, a, b):
        return a + b

class SubtractionTool(BaseTool):
    """Tool to subtract one number from another."""
    def use_tool(self, a, b):
        return a - b

# Instantiate Each Tool
addition_tool_name = "add_numbers"
addition_tool_description = "Add two numbers, a and b, together. For example, add_numbers(a=10, b=12) -> 22. Numbers can be any rational number.
addition_tool_parameters = [
    {"name": "a", "type": "float", "description": "The first number to add, such as 5"},
    {"name": "b", "type": "float", "description": "The second number to add, such as 4.6"}
]

subtraction_tool_name = "subtract_numbers"
subtraction_tool_description = "Perform subtraction of one number (b) from another (a) yielding a-b. For example, subtract_numbers(a=8, b=5) -> 3. Numbers can be any rational number.
subtraction_tool_parameters = [
    {"name": "a", "type": "float", "description": "The minuend, such as 5"},
    {"name": "b", "type": "float", "description": "The subtrahend, such as 9"}
]

addition_tool = AdditionTool(addition_tool_name, addition_tool_description, addition_tool_parameters)
subtraction_tool = SubtractionTool(subtraction_tool_name, subtraction_tool_description, subtraction_tool_parameters)

# Instantiate ToolUser by Passing it Tool Instances 
math_tool_user = ToolUser([addition_tool, subtraction_tool])

# Use Claude With the Provided Tools
math_tool_user.use_tools("Sally has 17 apples. She gives 9 to Jim. Later that day, Peter gives 6 Banans to Sally. How many pieces of fruit does Sally have at the end of the day?")
```
## Examples
Now that you know about BaseTool and ToolUser, we recommend going through some examples of common use cases and more advanced usage patterns, which can be found in the `examples` folder. Head over to [EXAMPLES.md](tool_use_package/examples/EXAMPLES.md) for a walkthrough:  
- [Give Claude access to an API](tool_use-_package/examples/EXAMPLES.md#api-example)
- [Let Claude call a SQL database](tool_use_package/examples/EXAMPLES.md#sql-example)
- [Let Claude search across a variety of data sources](tool_use_package/examples/EXAMPLES.md#search-example)