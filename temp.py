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
    print(f"🔍 Инструменты для ISIN {isin}:")
    for instr in instruments:
        print(f"  FIGI={instr.figi} | ISIN={instr.isin} | Ticker={instr.ticker} | Name={instr.name}")
    for instr in instruments:
        if instr.isin == isin:
            print(f"✅ Найден FIGI для ISIN {isin}: {instr.figi}")
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
        print(f"FIGI: {pos.figi} | ISIN: {isin} | Количество: {pos.quantity.units} | Price: {price:.2f}")

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
        total = money_value_to_decimal(portfolio.total_amount_portfolio)

        # Получаем FIGI по ISIN
        # Получаем FIGI по ISIN для облигаций (берём первый, там один вариант)
        figi_bonds = get_figi(client, ISIN_BONDS)

        # Для акций жёстко задаём FIGI из портфеля, чтобы избежать ошибки выбора
        figi_stocks = "TCS60A101X76"
        print(f"DEBUG: Используем вручную FIGI акций: {figi_stocks}")
        print(f"DEBUG: Полученный FIGI облигаций: {figi_bonds}")

        # Считаем стоимости позиций
        total_stocks = Decimal("0")
        total_bonds = Decimal("0")

        for p in portfolio.positions:
            price = get_market_price(client, p.figi)
            qty = int(p.quantity.units)  # приводим к int
            value = Decimal(qty) * price

            print(f"DEBUG: FIGI={p.figi} | price={price} | qty={qty} | value={value}")

            if p.figi.upper() == figi_stocks.upper():
                total_stocks += value
            elif p.figi.upper() == figi_bonds.upper():
                total_bonds += value

        target = total / 2
        diff_stocks = target - total_stocks
        diff_bonds = target - total_bonds
        print(diff_stocks)
        print(diff_bonds)
        # Расчёт отклонения и направления
        diff = (total / 2) - total_stocks
        if abs(diff) < 100:
            print("⚖️ Отклонение < 100₽ — ребаланс не требуется.")
            return


        if diff_stocks > diff_bonds:
            if diff_bonds > 0:
                bond_price = get_market_price(client, figi_bonds)
                qty = (diff_bonds / bond_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_bonds, OrderDirection.ORDER_DIRECTION_BUY, int(qty))
            else:
                bond_price = get_market_price(client, figi_bonds)
                qty = (-diff_bonds / bond_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_bonds, OrderDirection.ORDER_DIRECTION_SELL, int(qty))


            if diff_stocks > 0:
                stock_price = get_market_price(client, figi_stocks)
                qty = (diff_stocks / stock_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_stocks, OrderDirection.ORDER_DIRECTION_BUY, int(qty))
            else:
                stock_price = get_market_price(client, figi_stocks)
                qty = (-diff_stocks / stock_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_stocks, OrderDirection.ORDER_DIRECTION_SELL, int(qty))
        else:
            if diff_stocks > 0:
                stock_price = get_market_price(client, figi_stocks)
                qty = (diff_stocks / stock_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_stocks, OrderDirection.ORDER_DIRECTION_BUY, int(qty))
            else:
                stock_price = get_market_price(client, figi_stocks)
                qty = (-diff_stocks / stock_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_stocks, OrderDirection.ORDER_DIRECTION_SELL, int(qty))
            if diff_bonds > 0:
                bond_price = get_market_price(client, figi_bonds)
                qty = (diff_bonds / bond_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_bonds, OrderDirection.ORDER_DIRECTION_BUY, int(qty))
            else:
                bond_price = get_market_price(client, figi_bonds)
                qty = (-diff_bonds / bond_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
                if qty > 0:
                    place_order(client, account_id, figi_bonds, OrderDirection.ORDER_DIRECTION_SELL, int(qty))

# 🚀 Старт
if __name__ == "__main__":
    rebalance()