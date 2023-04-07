from web3 import Web3,Account,contract
from flask import Flask
from time import sleep


# Connect to an Ethereum node
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/2880b501e9c24ae48f93452cc0406bd8'))
assert True is w3.is_connected()
# Load the contract bytecode and ABI from files
with open('Contract.bin', 'r') as f:
    bytecode = f.read()
with open('Contract.abi', 'r') as f:
    abi = f.read()
    
# Create a new account
account = Account.create()

# Print the account address and private key
print('Account address:', account.address)
print('Account private key:', account._private_key.hex())

# Create a contract instance
contract = w3.eth.contract(abi=abi, bytecode=bytecode, address=account.address)

app = Flask(__name__)


# Instantiate a new contract object using the loaded ABI and contract address

@app.route('/')
def index():
    # Call a contract function and return the result to the view
    # result = contract.functions.createProject('Reshma', 'Paddy', 2).call()
    # print(result)
    reg = contract.functions.register('Urmil').call()
    create_prod = contract.functions.createProject('Reshma', 'Paddy', 2).call()
    result = contract.functions.returnProj(1).call()
    return str(result)

if __name__ == '__main__':
    app.run()