import os
from dotenv import load_dotenv
from tinkoff.invest import (
    Client, InstrumentIdType, OrderDirection, OrderType, Quotation
)
from decimal import Decimal, ROUND_DOWN
load_dotenv()
TOKEN_TIN = os.getenv("STRIPE_API_KEY")
TOKEN = TOKEN_TIN

ISIN_STOCKS = "RU000A101X76"   # ISIN БПИФа на акции
ISIN_BONDS  = "RU000A1039N1"   # ISIN БПИФа на облигации


def money_value_to_decimal(q: Quotation) -> Decimal:
    return Decimal(q.units) + Decimal(q.nano) / Decimal("1e9")

# 🔍 Получаем FIGI по ISIN
def get_figi(client, isin: str) -> str:
    instruments = client.instruments.find_instrument(query=isin).instruments
    for instr in instruments:
        if instr.isin == isin:
            return instr.figi
    raise Exception(f"❌ FIGI по ISIN {isin} не найден")

# 💵 Получаем цену по FIGI
def get_market_price(client, figi: str) -> Decimal:
    prices = client.market_data.get_last_prices(figi=[figi]).last_prices
    for p in prices:
        if p.figi == figi:
            return money_value_to_decimal(p.price)
    raise ValueError(f"❌ Не удалось получить цену для FIGI {figi}")

# 📊 Получаем первый брокерский счёт (не ИИС)
def get_account_id(client) -> str:
    accounts = client.users.get_accounts().accounts
    for acc in accounts:
        if acc.access_level.name == "ACCOUNT_ACCESS_LEVEL_FULL_ACCESS":
            return acc.id
    raise Exception("❌ Нет подходящего брокерского счёта")

# 📦 Получаем портфель
def get_portfolio(client, account_id):
    return client.operations.get_portfolio(account_id=account_id)

# 📋 Печатаем все позиции
def print_all_positions(client, portfolio):
    print("\n📋 Все позиции в портфеле:")
    for pos in portfolio.positions:
        try:
            instr = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=pos.figi
            ).instrument
            isin = instr.isin
        except:
            isin = ""
        price = get_market_price(client, pos.figi)
        print(f"FIGI: {pos.figi} | ISIN: {isin} | Qty: {pos.quantity.units} | Price: {price:.2f}")

# 🛒 Совершаем ордер
def place_order(client, account_id, figi, quantity: int, direction: OrderDirection):
    if quantity < 1:
        print("ℹ️ Кол-во лотов меньше 1 — пропуск.")
        return
    client.orders.post_order(
        figi=figi,
        quantity=quantity,
        direction=direction,
        account_id=account_id,
        order_type=OrderType.ORDER_TYPE_MARKET,
        order_id="",  # UUID сгенерируется автоматически
    )
    print(f"✅ Order_{direction.name.title()} {quantity} лотов по FIGI {figi}")

# 🔄 Главная логика ребалансировки
def rebalance():
    with Client(TOKEN) as client:
        print("\n🔄 Запуск ребалансировки")
        account_id = get_account_id(client)
        portfolio = get_portfolio(client, account_id)
        print_all_positions(client, portfolio)

        # Получаем FIGI по ISIN
        figi_stocks = get_figi(client, ISIN_STOCKS)
        figi_bonds = get_figi(client, ISIN_BONDS)

        # Считаем стоимости позиций
        total_stocks = Decimal("0")
        total_bonds = Decimal("0")
        for p in portfolio.positions:
            price = get_market_price(client, p.figi)
            value = Decimal(p.quantity.units) * price
            if p.figi == figi_stocks:
                total_stocks += value
            elif p.figi == figi_bonds:
                total_bonds += value

        total = total_stocks + total_bonds
        print(f"\n📊 Портфель: Акции = {total_stocks:.2f}₽ | Облигации = {total_bonds:.2f}₽ | Всего = {total:.2f}₽")

        # Расчёт отклонения и направления
        diff = (total / 2) - total_stocks
        if abs(diff) < 100:
            print("⚖️ Отклонение < 100₽ — ребаланс не требуется.")
            return

        # direction = OrderDirection.ORDER_DIRECTION_BUY if diff > 0 else OrderDirection.ORDER_DIRECTION_SELL
        #
        # # Получаем цену и количество лотов
        # stock_price = get_market_price(client, figi_stocks)
        # qty = (abs(diff) / stock_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
        #
        # place_order(client, account_id, figi_stocks, int(qty), direction)

# 🚀 Старт
if __name__ == "__main__":
    rebalance()