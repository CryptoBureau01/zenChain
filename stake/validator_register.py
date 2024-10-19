import sys
from web3 import Web3
import time

# ANSI escape codes for green text
GREEN = "\033[92m"
RESET = "\033[0m"  # Reset to default color


# Set the ZenChain RPC URL
rpc_url = "http://localhost:9944"

# Load data from priv-data.txt
file_path = "/root/chain-data/chains/priv-data.txt"

try:
    with open(file_path, 'r') as file:
        data = file.readlines()
        MY_ADDRESS = data[0].split('=')[1].strip()
        PRIVATE_KEY = data[1].split('=')[1].strip()
        SESSION_KEYS = data[2].split('=')[1].strip()
except FileNotFoundError:
    print("Private data file not found!")
    sys.exit(1)
except IndexError:
    print("Failed to load MY_ADDRESS, PRIVATE_KEY, or SESSION_KEYS from priv-data.txt.")
    sys.exit(1)

if SESSION_KEYS.startswith("0x"):
    SESSION_KEYS = SESSION_KEYS[2:]

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(rpc_url))



# Check if connected to the ZenChain network
if not w3.is_connected():
    print('Not connected to ZenChain')
    sys.exit(1)

if not w3.is_address(MY_ADDRESS):
    print(f"Invalid address: {MY_ADDRESS}")
else:
    try:
        balance = w3.eth.get_balance(MY_ADDRESS)
        balance_in_ether = w3.from_wei(balance, 'ether')
        print(f"{GREEN}Balance for {MY_ADDRESS}: {balance_in_ether} ZCX{RESET}")
    except Exception as e:
        print(f"Error getting balance: {e}")



NATIVE_STAKING_ADDRESS = '0x0000000000000000000000000000000000000800'
NATIVE_STAKING_ABI = [
    {
        'inputs': [{'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}],
        'name': 'bondExtra',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function'
    },
    {
        'inputs': [{'internalType': 'uint32', 'name': 'commission', 'type': 'uint32'},
                   {'internalType': 'bool', 'name': 'blocked', 'type': 'bool'}],
        'name': 'validate',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function'
    },
]


staking_contract = w3.eth.contract(address=NATIVE_STAKING_ADDRESS, abi=NATIVE_STAKING_ABI)

CHAIN_ID = 8408
nonce = w3.eth.get_transaction_count(MY_ADDRESS)


def send_transaction(func):

    transaction = func.build_transaction({
        'chainId': CHAIN_ID,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    print(f"Transaction sent. Hash: {tx_hash.hex()}")
    
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt['status'] == 1:
        print("Transaction successful!")
    else:
        print("Transaction failed.")
    
    return tx_hash

def increase_stake_and_validate(additional_stake_zcx, commission_rate=0, blocked=False):
    additional_stake_wei = int(additional_stake_zcx * 10**18)
    
    print(f"Step 1: Adding {additional_stake_zcx} ZCX to existing stake...")
    bond_extra_function = staking_contract.functions.bondExtra(additional_stake_wei)
    send_transaction(bond_extra_function)
    
    time.sleep(10)
    
    print(f"Step 2: Activating as validator with {commission_rate/10000000}% commission...")
    validate_function = staking_contract.functions.validate(commission_rate, blocked)
    send_transaction(validate_function)
    
    print("Validator Register Process completed!")

if __name__ == "__main__":
    additional_stake = 2 
    commission_rate = 50000000  
    increase_stake_and_validate(additional_stake, commission_rate)

