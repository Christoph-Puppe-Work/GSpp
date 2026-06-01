from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

def my_func(a: str, tool_context: ToolContext):
    pass

try:
    tool = FunctionTool(func=my_func)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
