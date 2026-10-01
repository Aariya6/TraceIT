from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_version:str='5.0.0'
    database_url:str='sqlite:///./traceit.db'
    cors_origins:str='http://localhost:4173,http://localhost:5500,http://127.0.0.1:4173,http://127.0.0.1:5500'
    auth_secret:str='CHANGE_ME'
    auth_token_hours:int=72
    environment:str='development'
    model_artifact:str='artifacts/traceit_neural.pt'
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
