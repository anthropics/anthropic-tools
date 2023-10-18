# Import required external packages
import sqlite3 # Change this to whatever package you need for making your conn string.
import os # For deleting our db file at the end

# Import the requisite BaseTool and ToolUser classes, as well as some helpers.
from ..base_tool import BaseTool
from ..tool_user import ToolUser
from ..prompt_constructors import construct_format_sql_tool_for_claude_prompt

# Define our custom SQL Tool by inheriting BaseTool and defining its use_tool() method. In this case we also override its format_tool_for_claude method to provide some additional detail.
class SQLTool(BaseTool):
    """A tool that can run SQL queries against a datbase. db_conn should be a connection string such as sqlite3.connect('test.db')"""

    def __init__(self, name, description, parameters, db_schema, db_conn, db_dialect):
        super().__init__(name, description, parameters)
        self.db_schema = db_schema
        self.db_conn = db_conn
        self.db_dialect = db_dialect

    
    def use_tool(self, sql_query):
        """Executes a query against the given database connection."""
       
        cursor = self.db_conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        cursor.close()

        return results
    
    def format_tool_for_claude(self):
        """Overriding the base class format_tool_for_claude in this case, which we don't always do. Returns a formatted representation of the tool suitable for the Claude system prompt.""" #TODO: Test if we even need to do this vs putting schema in the description.
        
        return construct_format_sql_tool_for_claude_prompt(self.name, self.description, self.parameters, self.db_schema, self.db_dialect)

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
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
    
    sql_tool = SQLTool(tool_name, tool_description, tool_parameters, tool_db_schema, tool_db_conn, tool_db_dialect)

    # Pass the tool instance into the ToolUser
    tool_user = ToolUser([sql_tool])

    print(tool_user.use_tools("Who is our oldest employee?", single_function_call=False))

    # Delete the temporary db
    os.remove('test.db')
