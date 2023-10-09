from abc import ABC, abstractmethod

from .prompt_constructors import construct_format_tool_for_claude_prompt

# We define an abstract base class for a tool that users can inherit to define any tool which can be expressed as a python function.
# TODO: Right now our implementation does not accept optional parameters. Add support for these.
# TODO: Right now your parameters specification only can specify the top type, and can not specify the type of nested values. Should adjust this.
class BaseTool(ABC):
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    def use_tool(self):
        pass
    
    def format_tool_for_claude(self):
        return construct_format_tool_for_claude_prompt(self.name, self.description, self.parameters)