import pydantic
from typing import Annotated
from google.adk.agents.invocation_context import InvocationContext
from pydantic.json_schema import SkipJsonSchema

def my_func(a: str, ctx: Annotated[InvocationContext, SkipJsonSchema]):
    pass

from google.adk.tools import FunctionTool
try:
    tool = FunctionTool(func=my_func)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
