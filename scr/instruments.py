# Справочная информация о ценных бумагах
import os
from dotenv import load_dotenv
from tinkoff.invest import Client

load_dotenv()
TOKEN_TIN = os.getenv("STRIPE_API_KEY")
