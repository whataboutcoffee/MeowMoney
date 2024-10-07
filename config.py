from environs import Env

from dataclasses import dataclass
from typing import Optional


@dataclass
class BotConfig:
    """Keeps bot parameters from the .env file"""
    token: str
    admin_ids: list

@dataclass
class DBConfig:
    server: str
    username: str
    database: str
    port: str
    password: str


class Config:
    def __init__(self, path: Optional[str] = None) -> None:
        """For keeping all configurations from the .env file in one place (for the bot itself, database, etc.)
        Parameters:
            path: str | None = None - path to the .env file
        """
        env = Env()
        env.read_env(path)
        self.bot = BotConfig(token=env('BOT_TOKEN'), admin_ids=env.list('ADMIN_IDS'))
        self.db = DBConfig(server=env('SERVER'),
                           username=env('USER'),
                           database=env('DATABASE'),
                           port=env('PORT'),
                           password=env('PASSWORD'))
