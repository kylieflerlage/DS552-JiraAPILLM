from dataclasses import dataclass

@dataclass
class Config:
    base_url:str   
    email: str
    api_token: str
    