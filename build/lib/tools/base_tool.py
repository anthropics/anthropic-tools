from abc import ABC, abstractmethod

from ..prompt_constructors import construct_format_tool_for_claude_prompt

class BaseTool(ABC):
    """
    An abstract base class for defining custom tools that can be represented as Python functions.
    
    Attributes:
    -----------
    - name (str): The name of the tool.
    - description (str): A short description of what the tool does.
    - parameters (list): A list of parameters that the tool requires, each parameter should be a dictionary with 'name', 'type', and 'description' key/value pairs.

    Notes/TODOs:
    ------
    - Currently, this implementation does not support optional parameters.
    - Currently, the parameters specification can only specify the top type and cannot define the type of nested values.

    Usage:
    ------
    To use this class, you should subclass it and provide an implementation for the `use_tool` abstract method.
    """

    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    def use_tool(self):
        """Abstract method that should be implemented by subclasses to define the functionality of the tool."""
       
        pass
    
    def format_tool_for_claude(self):
        """Returns a formatted representation of the tool suitable for the Claude system prompt."""
        
        return construct_format_tool_for_claude_prompt(self.name, self.description, self.parameters)