from pydantic import BaseModel

class ModuleConfig(BaseModel):
    name: str
    version: str
    description: str
    author: str
