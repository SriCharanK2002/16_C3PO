from flask import Flask, jsonify
from web3 import Web3

app = Flask(__name__)

# Connect to an Ethereum node
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/<your_infura_project_id>'))

# Load the contract ABI
with open('Contract.abi', 'r') as f:
    abi = f.read()

# Load the contract by address and ABI
contract_address = '0x1234567890123456789012345678901234567890'
contract = w3.eth.contract(address=contract_address, abi=abi)

@app.route('/get_data', methods=['GET'])
def get_data():
    # Call the contract function and get the result
    data = contract.functions.get_data().call()

    # Return the result as a JSON response
    return jsonify({'data': data})

if __name__ == '__main__':
    app.run()

