from web3 import Web3
import requests
import os
import httpx
import asyncio
from dotenv import load_dotenv
from tqdm.asyncio import tqdm as tqdm_asyncio

load_dotenv()  # take environment variables from .env.

# Connect to Infura
ethscan_api_url = "https://api.etherscan.io/api"
api_key = os.getenv('API_KEY')
infura_key = os.getenv('IN_KEY')
w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))

target_address = "0xDCe5d6b41C32f578f875EfFfc0d422C57A75d7D8" #change this to what you want to search

async def get_message(hash):
    loop = asyncio.get_running_loop()

    def get_transaction_sync():
        return w3.eth.get_transaction(hash)

    try:
        tx2 = await loop.run_in_executor(None, get_transaction_sync)

        if not tx2 or 'input' not in tx2:
            print("Transaction not found or doesn't have an input field")
            return ''
        hex_string = tx2['input']
        if hex_string.startswith('0x'):
            hex_string = hex_string[2:]
        if len(hex_string) >= 1:
            #print(f"Transaction Hash: https://etherscan.io/tx/{hash}\n", bytes.fromhex(hex_string).decode('utf-8'))
            decoded_data = bytes.fromhex(hex_string).decode('utf-8', errors='ignore')
            return f"***\nTransaction Hash: https://etherscan.io/tx/{hash}\n{decoded_data}\n***\n\n"
        return ""
    except Exception as e:
        return ""

async def get_transactions(address, api_key):
    parameters = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 29999999,
        "page": 1,
        "offset": 10000,
        "sort": "asc",
        "apikey": api_key}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(ethscan_api_url, params=parameters)

    if response.status_code == 200:
        result = response.json()
        if result['status'] == '1':
            filename = f"data tx for {target_address}.txt"
            with open(filename, 'a') as file:
                if result['result']:
                    tasks = [get_message(tx['hash']) for tx in result['result']]
                    messages = []
                    for future in tqdm_asyncio.as_completed(tasks, desc="Processing Transactions", total=len(tasks)):
                        message = await future
                        messages.append(message)
                    with open(filename, 'w') as file:
                        for message in messages:
                            file.write(message)
                elif result['message'] == "No transactions found":
                    print('No transactions found for address', address)
                else:
                    return []
        else:
            raise Exception('Request failed with message: {}'.format(result['message']))
    else:
        raise Exception('Request failed with status code: {}'.format(response.status_code))

async def main():
    await get_transactions(f"{target_address}", api_key)

asyncio.run(main())
