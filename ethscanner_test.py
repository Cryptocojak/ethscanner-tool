import requests
import time
from datetime import datetime
import xlsxwriter
import pandas as pd


api_key = 'K4MJCAZ9H7W7VBTTPD1JUR2VPXHFJM7ZMW' # replace with your API key
ethscan_addy_url = 'https://etherscan.io/address/'

save_as = input('what would you like to save this as? ')
name_of_project = '_' + save_as + '.xlsx'
workbook = xlsxwriter.Workbook(name_of_project)
worksheet = workbook.add_worksheet()

def convert_timestamp(timestamp):
    # Try converting Unix timestamp to datetime
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    # If conversion fails, return the timestamp as it is
    except ValueError:
        return timestamp



def get_balance(address, api_key):
    url = "https://api.etherscan.io/api"
    parameters = {
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
        "apikey": api_key
    }
    
    response = requests.get(url, params=parameters)
    
    if response.status_code == 200:
        result = response.json()
        if result['status'] == '1':
            # The result is given in Wei, so we convert it to Ether
            balance = int(result['result']) / 10**18
            return balance
        else:
            raise Exception('Request failed with message: {}'.format(result['message']))
    else:
        raise Exception('Request failed with status code: {}'.format(response.status_code))

def get_internal_transactions(address, api_key):
    url = "https://api.etherscan.io/api"
    parameters = {
        "module": "account",
        "action": "txlistinternal",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "offset": 1000,
        "apikey": api_key
    }

    response = requests.get(url, params=parameters)

    if response.status_code == 200:
        result = response.json()
        if result['status'] == '1':
            if result['result']:
                transactions = [(tx['hash'], int(tx['value']) / 10**18, tx['blockNumber'], tx['timeStamp'], (tx['to']) if tx['from'].lower() == address.lower() else (tx['from']), 'Internal Tx Out' if tx['from'].lower() == address.lower() else 'Internal Tx In') for tx in result['result']]
                return transactions
            else:
                return []
        elif result['message'] == "No transactions found":
            return []
        else:
            raise Exception('Request failed with message: {}'.format(result['message']))
    else:
        raise Exception('Request failed with status code: {}'.format(response.status_code))


def get_transactions(address, api_key):
    url = "https://api.etherscan.io/api"
    parameters = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10000,
        "sort": "asc",
        "apikey": api_key
    }

    response = requests.get(url, params=parameters)

    if response.status_code == 200:
        result = response.json()
        if result['status'] == '1':
            # Check if there are any transactions
            if result['result']:
                # For simplicity, let's just store some key information for each transaction
                transactions = [(tx['hash'],
                                int(tx['value']) / 10**18,
                                tx['blockNumber'],
                                tx['timeStamp'],
                                (tx['to']) if tx['from'].lower() == address.lower() else (tx['from']),
                                'Out to' if tx['from'].lower() == address.lower() else 'In from') for tx in result['result']]
                return transactions
            
            elif result['message'] == "No transactions found":
                print('No transactions found for address', address)
                return []
            else:
                # No transactions for this address
                return []
        else:
            raise Exception('Request failed with message: {}'.format(result['message']))
    else:
        raise Exception('Request failed with status code: {}'.format(response.status_code))

# Open the text file and read the addresses
input_file = input('what is your txt file called?\n')
with open(input_file, 'r') as file:
    words = file.read().split()
    addresses = list(set(word for word in words if word.startswith('0x')))

# Prepare list for saving results
results = []
# Create workbook
workbook = xlsxwriter.Workbook(name_of_project)

# Get balance for each address
for address in addresses:
    try:
        balance = get_balance(address, api_key)
        print('Balance for address', address, ':', balance, 'ETH')
        results.append((address, balance))

        transactions = get_transactions(address, api_key)
        internal_transactions = get_internal_transactions(address, api_key)
        all_transactions = transactions + internal_transactions
        all_transactions = sorted(all_transactions, key=lambda tx: int(tx[3]), reverse=True)

        worksheet = workbook.add_worksheet(address[:30])  # Worksheet name must be <= 31 chars, so we truncate the address
        # Create a format to use to highlight cells
        center_format = workbook.add_format({'align': 'center', 'text_wrap': True})

        worksheet.write('A1', 'BlockNumber')
        worksheet.write('B1', 'Transaction Hash')
        worksheet.write('C1', 'Timestamp')
        worksheet.write('D1', 'Amount')
        worksheet.write('F1', 'Address')
        worksheet.write('E1', 'Direction')
        worksheet.write('J1', 'Address:')
        worksheet.write('I1', 'Balance (ETH)')
        worksheet.write_url('J2', 'https://etherscan.io/address/' + address, string=address)
        worksheet.write_url('J3', 'https://etherscan.io/address/' + address, string='ethscan')
        worksheet.write_url('J4', 'https://debank.com/profile/' + address, string='debank')
        worksheet.write_url('J5', 'https://opensea.io/' + address, string='opensea')
        worksheet.write_url('J6', 'https://zapper.xyz/account/' + address, string='zapper')
        worksheet.write('I2', balance)

        worksheet.set_column('A:A', 11, center_format)
        worksheet.set_column('B:B', 65, center_format)
        worksheet.set_column('C:D', 10, center_format)
        worksheet.set_column('E:E', 10, center_format)
        worksheet.set_column('F:F', 45, center_format)
        worksheet.set_column('G:H', 3, center_format)
        worksheet.set_column('I:I', 10, center_format)
        worksheet.set_column('J:J', 45)

        for i, transaction in enumerate(all_transactions, start=2):
            worksheet.write_url('B'+str(i), 'https://etherscan.io/tx/' + transaction[0], string=transaction[0])
            worksheet.write('D'+str(i), transaction[1])
            worksheet.write('A'+str(i), transaction[2])
            worksheet.write('C'+str(i), convert_timestamp(transaction[3]))
            worksheet.write_url('F'+str(i), ethscan_addy_url + transaction[4], string=transaction[4])
            worksheet.write('E'+str(i), transaction[5])

    except Exception as e:
        print('Failed to get balance for address', address, '. Error:', str(e))

        # Sleep for a short period to prevent hitting rate limits
        time.sleep(1)

# Sort results by balance in descending order
results.sort(key=lambda x: x[1], reverse=True)

# Save results to a xlsx file
worksheet = workbook.add_worksheet('balances' + name_of_project)
center_format = workbook.add_format({'align': 'center'})

worksheet.write('A1', 'Address')
worksheet.write('B1', 'Balance')
worksheet.set_column('A:A', 64)
worksheet.set_column('B:B', 12, center_format)


for i, result in enumerate(results, start=2):
    worksheet.write('A'+str(i), 'https://etherscan.io/address/' + result[0])
    worksheet.write('B'+str(i), result[1])

workbook.close()

def convert_to_csv(filename_from_):
# Load spreadsheet
    xl = pd.ExcelFile(filename_from_)

    # Loop over all sheets in the workbook
    for sheet_name in xl.sheet_names:
        # Load a sheet into a DataFrame
        df = xl.parse(sheet_name)

        # Create a unique file name for each sheet
        csv_file_name = f"{sheet_name}.csv"

        # Save DataFrame to csv
        df.to_csv(csv_file_name, index=False)

#convert_to_csv(name_of_project)