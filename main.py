from tinkoff.invest import Client



if __name__ == '__main__':


    TOKEN = 'token'

    with Client(TOKEN) as client:
        print(client.users.get_accounts())