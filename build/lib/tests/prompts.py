test_use_tools_prompt = """In this environment you have access to a set of tools you can use to answer the user's question.

You may call them like this:
<function_calls>
<invoke>
<tool_name>$TOOL_NAME</tool_name>
<parameters>
<$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>
...
</parameters>
</invoke>
</function_calls>

Here are the tools available:
<tools>
<tool_description>
<tool_name>get_weather</tool_name>
<description>
The get_weather tool will return weather data for a given city, including temperature and wind speed.
</description>
<parameters>
<parameter>
<name>city</name>
<type>str</type>
<description>The city for which you would like the weather.</description>
</parameter>
</parameters>
</tool_description>
</tools>

Human: I live in San Francisco, what shold I wear today?

Assistant:"""

test_successful_function_run_injection_prompt = """<function_results>
<result>
<tool_name>perform_addition</tool_name>
<stdout>
8
</stdout>
</result>
</function_results>"""

test_error_function_run_injection_prompt = """<function_results>
<system>
Missing required parameters a for <tool_name>perform_addition</tool_name>.
</system>
</function_results>"""

test_format_tool_for_claude_prompt = """<tool_description>
<tool_name>get_weather</tool_name>
<description>
The get_weather tool will return weather data for a given city, including temperature and wind speed.
</description>
<parameters>
<parameter>
<name>city</name>
<type>str</type>
<description>The city for which you would like the weather.</description>
</parameter>
</parameters>
</tool_description>"""

test_format_sql_tool_for_claude_prompt = """<tool_description>
<tool_name>execute_sqlite3_query</tool_name>
<description>
The execute_sqlite3_query tool will execute a given sql query against a sql database with the provided schema and return the results of that query. It will return to you the results of that query.
The database uses SQLite dialect. The schema of the database is provided to you here:
<schema>
CREATE TABLE employee_data (
          id INTEGER PRIMARY KEY, 
          name TEXT NOT NULL,
          age INTEGER NOT NULL
          )
</schema>
</description>
<parameters>
<parameter>
<name>sql_query</name>
<type>str</type>
<description>The query to run.</description>
</parameter>
</parameters>
<important_usage_notes>
* When invoking this tool, the contents of the 'query' parameter does NOT need to be XML-escaped.
</important_usage_notes>
</tool_description>"""