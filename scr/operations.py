# Сервис получения информации о портфеле по конкретному счёту
import os
from dotenv import load_dotenv
from tinkoff.invest import Client

load_dotenv()
TOKEN_TIN = os.getenv("STRIPE_API_KEY")
TOKEN = TOKEN_TIN


def get_portfolio(id):
    """Получить список позиций по счёту.статистическую информацию по портфелю — абсолютные и относительные доходности, текущую стоимость активов"""
    with Client(TOKEN) as client:
        portfolio = client.operations.get_portfolio(account_id=id)

        return portfolio


def get_positions(id):
    """Получить список позиций по счёту."""
    with Client(TOKEN) as client:
        positions = client.operations.get_positions(account_id=id)

        return positions
