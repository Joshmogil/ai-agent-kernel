from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Literal


file_type = Literal['ignore', 'code', 'data', 'knowledge']
def classify_files(directory: str)-> dict[str, file_type]:
    pass
#class 

#agent: Agent = Agent(model="gemini-1.5-flash")