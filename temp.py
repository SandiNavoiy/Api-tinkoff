import os
from dotenv import load_dotenv
from tinkoff.invest import Client

load_dotenv()
TOKEN_TIN = os.getenv("STRIPE_API_KEY")


TOKEN = TOKEN_TIN


def www():
    """Получить аккаунты"""
    with Client(TOKEN) as client:
        print(dir(client.operations))


www()
