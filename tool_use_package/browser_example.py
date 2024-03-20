# This contains the code for browser tool that opens a single webpage at a url
import html2text
import requests

from .tools.base_tool import BaseTool
from .tool_user import ToolUser

class BrowserTool(BaseTool):
  """Retrieves a webpage and formats to text for Claude"""

  def use_tool(self, url):
    try:
      response = requests.get(url)
      html = response.text
      h = html2text.HTML2Text()
      text = h.handle(html)
      return text
    except requests.exceptions.RequestException:
      return f"There was an error fetching {url}"

tool_name = "get_webpage"
tool_description = """The get_webpage tool will return the text of a webpage."""
tool_parameters = [
    {"name": "url", "type": "str", "description": "The URL of the webpage to get."}
]

browser_tool = BrowserTool(tool_name, tool_description, tool_parameters)

# Pass the tool instance into the ToolUser
tool_user = ToolUser([browser_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    messages = [{"role":"user", "content":f"Summarize http://docs.python.org"}]
    print(tool_user.use_tools(messages, execution_mode="automatic"))
