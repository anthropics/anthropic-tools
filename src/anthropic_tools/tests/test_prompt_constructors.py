import unittest

from ..prompt_constructors import (
    construct_use_tools_prompt,
    construct_successful_function_run_injection_prompt,
    construct_error_function_run_injection_prompt,
    construct_format_tool_for_claude_prompt,
    construct_format_sql_tool_for_claude_prompt,
    construct_prompt_from_messages
)
from .prompts import (
    test_use_tools_prompt,
    test_successful_function_run_injection_prompt,
    test_error_function_run_injection_prompt,
    test_format_tool_for_claude_prompt,
    test_format_sql_tool_for_claude_prompt
)

from ..weather_tool_example import weather_tool

# Should add multi-tool test cases for all/most of these
class TestPromptConstructors(unittest.TestCase):
    def test_construct_use_tools_prompt(self):
        tools = [weather_tool]
        self.assertEqual(construct_use_tools_prompt("\n\nHuman: I live in San Francisco, what shold I wear today?", tools, 'user'), test_use_tools_prompt)
    
    def test_construct_successful_function_run_injection_prompt(self):
        self.assertEqual(construct_successful_function_run_injection_prompt([{"tool_name": "perform_addition", "tool_result": 8}]), test_successful_function_run_injection_prompt)
    
    def test_construct_error_function_run_injection_prompt(self):
        self.assertEqual(construct_error_function_run_injection_prompt("Missing required parameters a for <tool_name>perform_addition</tool_name>."), test_error_function_run_injection_prompt)
    
    def test_construct_format_tool_for_claude_prompt(self):
        tool_name = "get_weather"
        tool_description = """The get_weather tool will return weather data for a given city, including temperature and wind speed."""
        tool_parameters = [
            {"name": "city", "type": "str", "description": "The city for which you would like the weather."} 
        ]
        self.assertEqual(construct_format_tool_for_claude_prompt(tool_name, tool_description, tool_parameters), test_format_tool_for_claude_prompt)
    
    def test_construct_format_sql_tool_for_claude_prompt(self):
        tool_name = "execute_sqlite3_query"
        tool_description = """The execute_sqlite3_query tool will execute a given sql query against a sql database with the provided schema and return the results of that query. It will return to you the results of that query."""
        tool_parameters = tool_parameters = [{"name": "sql_query", "type": "str", "description": "The query to run."}]
        # Indentation is important here.
        tool_db_schema = """CREATE TABLE employee_data (
          id INTEGER PRIMARY KEY, 
          name TEXT NOT NULL,
          age INTEGER NOT NULL
          )"""
        tool_db_dialect = 'SQLite'
        self.assertEqual(construct_format_sql_tool_for_claude_prompt(tool_name, tool_description, tool_parameters, tool_db_schema, tool_db_dialect), test_format_sql_tool_for_claude_prompt)

if __name__ == "__main__":
    unittest.main()