from ..base_tool import BaseTool
from ..tool_user import ToolUser
# Define our custom calculator tool
class CustomTool(BaseTool):
    # Would have a real calculator defined here.
    def use_tool(self, expression):
        return 45.75

# The user can then define their tool like so, and pass us an instance of it
tool_name = "evaluate_expression"
tool_description = """Evaluate mathematical expressions precisely using Python's math module.
- Supports any expression containing symbols such as *, /, +, -, and parentheses.
- Supports functions such as sin, cos, tan, factorial, sqrt, log, exp, and more. log can be given a base as a second argument like so: log(4,10).
- ** is used for exponentiation.
- Also supports constants such as pi and e.
Use this tool WHENEVER you need to perform any arithmetic calculation, as it will ensure your answer is precise."""

# TODO: Right not "type" must be the python type of the top-level and cannot specify anything else. Should look into expanding this.
tool_parameters = [
    {"name": "expression", "type": "str", "description": "The math expression to evaluate, such as 2*6+(37-3)**3*log(7, 10)"}
]

# Initialize an instance of your tool
my_custom_tool = CustomTool(tool_name, tool_description, tool_parameters)

# Pass the tool instance into the ToolUser
my_tool_user = ToolUser([my_custom_tool])

if __name__ == '__main__':
    print(my_tool_user.use_tools("A construction crew is building a wall that is 305 meters long and 3 meters high. If one worker can build 4 square meters per hour, how many total hours will it take 5 workers to build the wall?"))