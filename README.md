# anthropic-tools
A repo for using tools/function calling with Anthropic models.
### This SDK is Currently in Alpha and meant ONLY AS A RESEARCH PREVIEW. We promise no ongoing support. It is not intended for production use. Production-ready function calling support is coming to the Anthropic API soon.

## Setup
Set your Anthropic API key as an environment variable:  
```bash
# MacOS
export ANTHROPIC_API_KEY={your_anthropic_api_key}
```

If you are accessing Claude through AWS Bedrock, set the following enviroment variables instead:
```bash
# MacOS
export AWS_ACCESS_KEY_ID={your_AWS_access_key_id}
export AWS_SECRET_ACCESS_KEY={your_AWS_secret_access_key}
export AWS_SESSION_TOKEN={your_AWS_session_token}
```

[Optional] If you want to test the Brave search tool, set your Brave API key as an enviroment variable (get a key [here](https://api.search.brave.com/register)):
```bash
# MacOS
export BRAVE_API_KEY={your_brave_api_key}
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
anthropic-tools follows a very simple architecture that lets users define and use tools with Claude. There are two classes users should be familiar with: `BaseTool` and `ToolUser`.

Additionally, anthropic-tools introduces a new *structured* prompt format that you will want to pay close attention to. This should make for easier prompt construction and parsing.

anthropic-tools also supports a number of pre-built tools out of the box, built on top of the same primitives available to you. These are here in case you want even easier tool use for some of our most common tools, such as search or SQL.

### BaseTool
BaseTool is the class that should be used to define individual tools. All you need to do to create a tool is inherit `BaseTool` and define the `use_tool()` method for the tool.
```python
import datetime, zoneinfo
from tool_use_package.tools.base_tool import BaseTool

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

Then, you simply instantiate your custom tool with `name` (the name of the tool), `description` (the description Claude reads of what the tool does), and `parameters` (the parameters that the tool accepts). Pay attention to the formatting of each.
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
from tool_use_package.tool_user import ToolUser
time_tool_user = ToolUser([time_of_day_tool])
```

You can then make use of your ToolUser by calling its `use_tools()` method and passing in your desired prompt. Setting execution mode to "automatic" makes it execute the function; in the default "manual" mode it returns the function arguments back to the client to be executed there.
```python
messages = [{'role': 'user', 'content': 'What time is it in Los Angeles?'}]
time_tool_user.use_tools(messages, execution_mode='automatic')
```

If you are accesing Claude through AWS Bedrock, set the parameter `first_party` to `False` (it is by default set to `True`):
```python
time_tool_user = ToolUser([time_of_day_tool], first_party=False)
```
NOTE: If using bedrock, this SDK only supports claude 2.1 (anthropic.claude-v2:1).

Notice that new `messages` format instead of passing in a simple prompt string? Never seen it before? Don't worry, we are about to walk through it.

### Prompt Format
Anthropic-tools uses a *structured* prompt input and output format, coming as a list of messages, intending to mimic our Messages API format. Let's take a quick tour of how to work with this list.

`messages` is a python list of message dictionaries. A single message dictionary object can contain these fields but will never contain all of them (see the field comments below for more detail on what this means):
```python
{
    "role": str, # The role of the message. 'user' for a message from the user, 'assistant' for a message from the assistant, 'tool_inputs' for a request from the assistant to use tools, 'tool_outputs' for a response to a tool_inputs message containing the results of using the specified tools in the specified ways.
    "content": str, # The (non tool use) content of the message, which must be present for messages where role=(user, assistant, tool_inputs) and can not be present for messages where role=tool_outputs.
    "tool_inputs": list[dict], # A list of dictionaries (see below). Must be specified in messages where role=tool_inputs.
    "tool_outputs": list[dict], # A list of tool_output dictionaries (see below). One of tool_outputs or tool_error must be specified in messages where role=tool_outputs, but the other must be specified as None.
    "tool_error": str # A tool error message corresponding to the first tool that errored to help Claude understand what it did wrong. One of tool_error or tool_outputs must be specified when role=tool_outputs, but the other must be specified as None.
}
```

`tool_inputs` is a list of dictionaries, where each dictionary represents a tool to use (at the 'tool_name' key), and the arguments to pass to that tool (at the 'tool_arguments' key). A tool_inputs message might look something like this:
```python
{
    'role': 'tool_inputs',
    'content': '',
    'tool_inputs': [
        {
            'tool_name': 'perform_addition',
            'tool_arguments': {'a': 9, 'b': 1}
        },
        {
            'tool_name': 'perform_subtraction',
            'tool_arguments': {'a': 6, 'b': 4}
        }
    ]
}
```
Notice above that `tool_inputs` messages also have `content` attached to them, which can be the empty string but can also be content from the assistant that precedes the tool use request. These messages are rendered to Claude in the order `{content}{tool_inputs}`

The format of `tool_name` and `tool_arguments` is such that you can easily get results for the desired tool use by running the following code:
```python
tool = next((t for t in your_ToolUser_instance.tools if t.name == tool_name), None) # replace your_ToolUser_instance with your ToolUser instance
if tool is None:
    return "No tool named <tool_name>{tool_name}</tool_name> available."

return tool.use_tool(**tool_arguments)
```
> NOTE: While we have attempted to validate tool_arguments before returning them to you, you may still want to do some additional checks of tool_arguments before executing the function to check for things like malicious or invalid parameters. You can also do this inside of your use_tools method.

`tool_outputs` is also a list of dictionaries, where each dictionary represents the result of using the tool at the 'tool_name' key. The result is included at the 'tool_result' key. If we were responding to our above `tool_inputs` example, it might look something like this:
```python
{
    'role': 'tool_outputs',
    'tool_outputs': [ 
        {
            "tool_name": 'perform_addition',
            'tool_result': 10
        },
        {
            "tool_name": 'perform_subtraction',
            'tool_result': 2
        }
    ],
    'tool_error': None
}
```
> NOTE: It is highly recommended, but not required, that you provide tool_outputs *only for requested tool_inputs*, and that you provide them *in the same order as the tool_inputs*.  
> SECOND NOTE: Notice that `tool_outputs` messages do not have `content`. Trying to pass in content with a `tool_outputs` message will return an error.

Sometimes when Claude responds with a `tool_inputs` message it makes a mistake and either requests tools that do not exist or does not provide a valid set of parameters. While we try to catch this for you, it sometimes slips through the cracks. If any of Claude's `tool_inputs` are invalid you should stop parsing and send Claude back a message with a descriptive `tool_error` *instead of sending it `tool_outputs`*. Here is what a response message to an invalid `tool_inputs` message might look like.
```python
{
    'role': 'tool_outputs',
    'tool_outputs': None,
    'tool_error': 'Missing required parameter "b" in tool perform_addition.'
}
```

So, what might `messages` look like in practice?  
Here is a user message:
```python
user_message = {'role': 'user', 'content': 'Hi Claude, what US states start with C?'}
messages = [user_message]
```
Here is a user message and an assistant response, with no tool use involved.
```python
user_message = {'role': 'humuseran', 'content': 'Hi Claude, what US states start with C?'}
assistant_message = {'role': 'assistant', 'content': 'California, Colorado, and Connecticut are the US states that start with the letter C.'}
messages = [user_message, assistant_message]
```

Here is a user message, followed by a tool_inputs message, followed by a successful tool_outputs message:
```python
user_message = {'role': 'user', 'content': 'If Maggie has 3 apples and eats 1, how many apples does maggie have left?'}
tool_inputs_message = {
    'role': 'tool_inputs',
    'content': "Let's think this through. Maggie had 3 apples, she ate one so:",
    'tool_inputs': [{'tool_name': 'perform_subtraction', 'tool_arguments': {'a': 3, 'b': 1}}]
}
tool_outputs_message = {
    'role': 'tool_outputs',
    'tool_outputs': [{"tool_name": 'perform_subtraction', 'tool_result': 2}],
    'tool_error': None
}
messages = [user_message, tool_inputs_message, tool_outputs_message]
```

And here is what it would look like instead if Claude made a mistake and `perform_subtraction` failed.
```python
user_message = {'role': 'user', 'content': 'If Maggie has 3 apples and eats 1, how many apples does maggie have left?'}
tool_inputs_message = {
    'role': 'tool_inputs',
    'content': "Let's think this through. Maggie had 3 apples, she ate one so:",
    'tool_inputs': [{'tool_name': 'perform_subtraction', 'tool_arguments': {'a': 3}}]
}
tool_outputs_message = {
    'role': 'tool_outputs',
    'tool_outputs': None,
    'tool_error': 'Missing required parameter "b" in tool perform_subtraction.'
}
messages = [user_message, tool_inputs_message, tool_outputs_message]
```

That's it for the new messages format. To help wrap your head around this concept, at the end of the "Putting it Together" section below, we will build a python function to handle these sorts of requests.

### Putting it Together
Putting concepts one, two, and three together above, a full implementation with multiple tools might look something like this:
```python
from tool_use_package.base_tool import BaseTool
from tool_use_package.tool_user import ToolUser

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
addition_tool_name = "perform_addition"
addition_tool_description = "Add two numbers, a and b, together. For example, add_numbers(a=10, b=12) -> 22. Numbers can be any rational number."
addition_tool_parameters = [
    {"name": "a", "type": "float", "description": "The first number to add, such as 5"},
    {"name": "b", "type": "float", "description": "The second number to add, such as 4.6"}
]

subtraction_tool_name = "perform_subtraction"
subtraction_tool_description = "Perform subtraction of one number (b) from another (a) yielding a-b. For example, subtract_numbers(a=8, b=5) -> 3. Numbers can be any rational number."
subtraction_tool_parameters = [
    {"name": "a", "type": "float", "description": "The minuend, such as 5"},
    {"name": "b", "type": "float", "description": "The subtrahend, such as 9"}
]

addition_tool = AdditionTool(addition_tool_name, addition_tool_description, addition_tool_parameters)
subtraction_tool = SubtractionTool(subtraction_tool_name, subtraction_tool_description, subtraction_tool_parameters)

# Instantiate ToolUser by Passing it Tool Instances 
math_tool_user = ToolUser([addition_tool, subtraction_tool])

# Build messages
user_message = {
    "role": "user",
    "content": "Sally has 17 apples. She gives 9 to Jim. Later that day, Peter gives 6 Bananas to Sally. How many pieces of fruit does Sally have at the end of the day?"
}

messages = [user_message]

# Use Claude With the Provided Tools
math_tool_user.use_tools(messages, execution_mode='automatic')
```
This should return something like:
```python
{
    "role": "assistant",
    "content": "At the end of the day Sally has 14 pieces of fruit."
}
```

Astute observers may have noticed that they didn't see any of the function calling happen! That's because we used the `execution_mode='automatic'` argument when we called `use_tools()`. When this parameter is set to automatic, `use_tools` will handle all of the work of managing Claude's tool_inputs messages, executing your tools on the inputs, passing Claude errors, etc. It will only stop and return you a next message when it reaches a point that Claude does not make a tool use request (basically when it sends back a message with `role='assistant'`). This is a great mode for getting started with tool use, but abstracts away some customizability. Namely, using `execution_mode='automatic'` takes away your ability to do your own validation of the arguments Claude passes to your tools before calling use_tool() on them, your ability to finely control the errors you give back to Claude, and your ability to see the intermediate `tool_inputs` and `tool_outputs` messages that Claude and your tools are producing.

If you want all those things, you should instead call `use_tools()` with `execution_mode='manual'`.
```python
math_tool_user.use_tools(messages, execution_mode='manual')
```
This should return something like:
```python
{
    "role": "tool_inputs",
    "content": "Ok. Let's think through this in steps.\nSally has 17 apples.\nSally gives 9 apples to jim.\nso:\n",
    "tool_inputs": [
        {
            "tool_name": "perform_subtraction",
            "tool_arguments": {'a': 17, 'b': 9}
        }
    ]
}
```

Notice how this stops at the next message (in this case a `tool_inputs` message), and requires you to provide the `tool_outputs` message and pass in the new set of messages to keep going. Your next code would probably look something like this:
```python
claude_res = {
    "role": "tool_inputs",
    "content": "Ok. Let's think through this in steps.\nSally has 17 apples.\nSally gives 9 apples to jim.\nso:\n",
    "tool_inputs": [
        {
            "tool_name": "perform_subtraction",
            "tool_arguments": {'a': 17, 'b': 9}
        }
    ]
}

messages.append(claude_res)

next_message = {
    "role": "tool_outputs",
    "tool_outputs": [
        {
            "tool_name": "perform_subtraction",
            "tool_result": 8
        }
    ],
    "tool_error": None
}

messages.append(next_message)

math_tool_user.use_tools(messages, execution_mode='manual')
```

To wrap everything up, let's build a lightweight function that could automatically parse a response from Claude in manual mode, and generate the new messages list we want to pass to `use_tools()`. We will return a dictionary with two keys: `next_action`, which indicates if the next action should be to ask the user for input or to automatically respond to Claude with the results of its tool use request, and `messages`, which is the most up to date messages list.
```python
def handle_manual_claude_res(messages, claude_res, tool_user):
    """
    - messages does not include claude_res
    - tool_user should be the ToolUser instance you have been using for previous messages
    """
    # Append Claude's response to messages.
    messages.append(claude_res)
    
    if claude_res['role'] == "assistant":
        # If the message is not trying to use a tool we should not automatically respnd to Claude, and instead we should ask the user for input.
        return {"next_action": "user_input", "messages": messages}
    elif claude_res['role'] == "tool_inputs":
        # If the message is trying to use a tool we should parse the tool and arguments, use the tool, create the tool_outputs message with the results, and append that message to messages.
        tool_outputs = []
        for tool_input in claude_res['tool_inputs']:
            tool = next((t for t in tool_user.tools if t.name == tool_input['tool_name']), None)
            if tool is None:
                messages.append({"role": "tool_outputs", "tool_outputs": None, "tool_error": f"No tool named <tool_name>{tool_name}</tool_name> available."})
                return {"next_action": "auto_respond", "messages": messages}

            tool_result = tool.use_tool(**tool_input['tool_arguments'])
            tool_outputs.append({"tool_name": tool_input['tool_name'], "tool_result": tool_result})
        
        messages.append({"role": "tool_outputs", "tool_outputs": tool_outputs, "tool_error": None})
        return {"next_action": "auto_respond", "messages": messages}
    else:
        raise ValueError(f"Provided role should be assistant or tool_inputs, got {claude_res['role']}")
```

And that's it. You now know everything you need to know to give Claude tool use! For some more advanced techniques, exposure to some of our pre-built tools, and general inspiration check out our examples!

## Examples
Now that you know about `BaseTool`, `ToolUser`, and the new `messages` format, we recommend going through some examples of common use cases and more advanced usage patterns, which can be found in the `examples` folder. Head over to [EXAMPLES.md](tool_use_package/EXAMPLES.md) for a walkthrough:  
- [Give Claude access to an API](tool_use_package/EXAMPLES.md#api-example)
- [Let Claude call a SQL database](tool_use_package/EXAMPLES.md#sql-example)
- [Let Claude search across a variety of data sources](tool_use_package/EXAMPLES.md#search-example)
