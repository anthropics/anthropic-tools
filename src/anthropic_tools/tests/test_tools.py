import unittest
import os
import sqlite3

from ..calculator_example import addition_tool, subtraction_tool
from ..tools.sql_tool import SQLTool
from ..weather_tool_example import weather_tool

class TestCalculatorTools(unittest.TestCase):
    def test_addition_use_tool(self):
        use_result = addition_tool.use_tool(4, 6)
        self.assertIsInstance(use_result, (int, float))
        self.assertEqual(use_result, 10)
    
    def test_subtraction_use_tool(self):
        use_result = subtraction_tool.use_tool(4, 5.5)
        self.assertIsInstance(use_result, (int, float))
        self.assertEqual(use_result, -1.5)


class TestSQLTool(unittest.TestCase):
    def setUp(self):
        # Create a SQL database with a table to run our tool against
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
        
        # Initialize an instance of the tool
        tool_name = "execute_sqlite3_query"
        tool_description = """The execute_sqlite3_query tool will execute a given sql query against a sql database with the provided schema and return the results of that query. It will return to you the results of that query."""
        tool_parameters = tool_parameters = [{"name": "sql_query", "type": "str", "description": "The query to run."}]
        tool_db_schema = """CREATE TABLE employee_data (
          id INTEGER PRIMARY KEY, 
          name TEXT NOT NULL,
          age INTEGER NOT NULL
          )"""
        tool_db_conn = sqlite3.connect('test.db')
        tool_db_dialect = 'SQLite'
        
        self.sql_tool = SQLTool(tool_name, tool_description, tool_parameters, tool_db_schema, tool_db_conn, tool_db_dialect)
    
    def tearDown(self):
        os.remove('test.db')

    def test_sql_use_tool(self):
        use_result = self.sql_tool.use_tool("SELECT count(1) FROM employee_data")
        self.assertIsInstance(use_result, list)
        self.assertEqual(len(use_result), 1)
        self.assertEqual(use_result[0][0], 2)

class TestWeatherTool(unittest.TestCase):
    def test_weather_use_tool(self):
        use_result = weather_tool.use_tool("San Francisco")
        self.assertIsInstance(use_result, dict)

if __name__ == "__main__":
    unittest.main()