# Import required external packages
import sqlite3 # Change this to whatever package you need for making your conn string.
import os # For deleting our db file at the end

# Import the requisite BaseTool and ToolUser classes, as well as some helpers.
from .base_tool import BaseTool
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
        self.db_conn.commit()
        cursor.close()

        return results
    
    def format_tool_for_claude(self):
        """Overriding the base class format_tool_for_claude in this case, which we don't always do. Returns a formatted representation of the tool suitable for the Claude system prompt.""" #TODO: Test if we even need to do this vs putting schema in the description.
        
        return construct_format_sql_tool_for_claude_prompt(self.name, self.description, self.parameters, self.db_schema, self.db_dialect)