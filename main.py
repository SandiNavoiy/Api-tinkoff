from pprint import pprint

from scr.operations import get_portfolio, get_positions
from scr.users import account_id

if __name__ == "__main__":
    id = str(account_id())

    pprint(get_positions(id))
