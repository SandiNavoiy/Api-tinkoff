import os
from dotenv import load_dotenv
from tinkoff.invest import Client, InstrumentIdType, OrderDirection, OrderType, MoneyValue
from decimal import Decimal, ROUND_DOWN

import time
load_dotenv()
TOKEN_TIN = os.getenv("STRIPE_API_KEY")


TOKEN = TOKEN_TIN

ISIN_STOCKS = "RU000A101X76"   # ISIN БПИФа на акции
ISIN_BONDS  = "RU000A1039N1"   # ISIN БПИФа на облигации




# Функция: MoneyValue в Decimal
def money_value_to_decimal(value: MoneyValue) -> Decimal:
    return Decimal(value.units) + Decimal(value.nano) / Decimal("1e9")

# Получение account_id пользователя
def get_account_id(client):
    accounts = client.users.get_accounts()
    return accounts.accounts[0].id

# Поиск FIGI по ISIN
def get_figi(client, isin):
    instrument = client.instruments.find_instrument(query=isin)
    for item in instrument.instruments:
        if item.isin == isin:
            return item.figi
    raise Exception(f"FIGI по ISIN {isin} не найден.")

# Получение ISIN по FIGI (для отображения и сопоставления)
def get_isin_by_figi(client, figi):
    instrument = client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi)
    return instrument.instrument.isin

# Получение портфеля
def get_portfolio(client, account_id):
    return client.operations.get_portfolio(account_id=account_id)

# Цена по рынку
def get_market_price(client, figi):
    book = client.market_data.get_order_book(figi=figi, depth=1)
    return money_value_to_decimal(book.last_price)

# Отправка ордера
def place_order(client, account_id, figi, direction, quantity):
    order = client.orders.post_order(
        order_id="rebalance_" + figi,
        figi=figi,
        account_id=account_id,
        quantity=quantity,
        direction=direction,
        order_type=OrderType.ORDER_TYPE_MARKET
    )
    print(f"  ✅ {direction.name.title()} {quantity} лотов {figi}")

# Печать всех позиций
def print_all_positions(client, portfolio):
    print("\n📋 Все позиции в портфеле:")
    for p in portfolio.positions:
        price = money_value_to_decimal(p.current_price)
        isin = get_isin_by_figi(client, p.figi)
        print(f"FIGI: {p.figi} | ISIN: {isin} | Qty: {p.quantity.units} | Price: {price:.2f}")

# Ребалансировка
def rebalance():
    with Client(TOKEN) as client:
        print("🔄 Запуск ребалансировки")
        account_id = get_account_id(client)
        figi_stocks = get_figi(client, ISIN_STOCKS)
        figi_bonds = get_figi(client, ISIN_BONDS)

        portfolio = get_portfolio(client, account_id)
        print_all_positions(client, portfolio)

        total = money_value_to_decimal(portfolio.total_amount_portfolio)

        stocks_value = Decimal(0)
        bonds_value = Decimal(0)

        for p in portfolio.positions:
            value = money_value_to_decimal(p.current_price) * Decimal(p.quantity.units)
            isin = get_isin_by_figi(client, p.figi)
            if isin == ISIN_STOCKS:
                stocks_value += value
            elif isin == ISIN_BONDS:
                bonds_value += value

        print(f"\n📊 Портфель: Акции = {stocks_value:.2f}₽ | Облигации = {bonds_value:.2f}₽ | Всего = {total:.2f}₽")

        target = total / 2
        diff_stocks = target - stocks_value
        diff_bonds  = target - bonds_value
        print(diff_stocks)
        print(diff_bonds)

        if abs(diff_stocks) < Decimal(target/20):
            print("⚖️ Ребалансировка не требуется.")
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


if __name__ == "__main__":
    print("⏳ Ожидание расписания...")
    rebalance()
    print('')
