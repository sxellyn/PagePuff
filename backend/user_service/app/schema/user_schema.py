from pydantic import BaseModel

class AddUser(BaseModel):
    username: str
    email: str
    password: str
