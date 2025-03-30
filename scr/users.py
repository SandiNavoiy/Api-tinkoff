import os
from dotenv import load_dotenv
from tinkoff.invest import Client

load_dotenv()
TOKEN_TIN = os.getenv("STRIPE_API_KEY")

# Получить информацию о пользователе и его счетах в Т-Инвестициях

TOKEN = TOKEN_TIN


def get_accounts():
    """Получить аккаунты"""
    with Client(TOKEN) as client:
        accounts = client.users.get_accounts()

        return accounts


def get_info():
    """Получить инфо о пользователе"""
    with Client(TOKEN) as client:
        info = client.users.get_info()

        return info


def get_user_tariff():
    """Получить тариф"""
    with Client(TOKEN) as client:
        tarif = client.users.get_user_tariff()

        return tarif


def account_id():
    """Нахождение ID пользователя"""
    with Client(TOKEN) as client:
        accounts = client.users.get_accounts()
        return accounts.accounts[0].id
