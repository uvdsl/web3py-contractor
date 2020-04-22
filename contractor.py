from web3 import Web3, HTTPProvider
from datetime import datetime
import json

# CONNECTION = 'http://localhost:8543'

def log(message):
    print('==', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '==', message)

connection = input('== ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' == Connection: ')
try:
    log('Connecting to Geth at ' + connection + ' ...')
    w3 = Web3(HTTPProvider(connection))
    log('Connected at block: ' + str(w3.eth.blockNumber))
except:
    log('Did not reach Geth at ' + connection + ' ...')
else:
    # Read in contract name
    ctrct_name = input('== ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' == Contract Name: ')
    log('Contract: ' + str(ctrct_name))
    # Display account to use
    w3.eth.defaultAccount = w3.eth.accounts[0]
    log('Account: ' + w3.eth.defaultAccount)
    # Read in passphrase
    passphrase = input('== ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' == Passphrase: ')
    log('Unlock: ' + str(w3.geth.personal.unlockAccount(w3.eth.defaultAccount, passphrase)))
    # Read abi and bin
    with open('./data/abi/'+ctrct_name+'.abi', 'r') as file_ctrct_abi:
        ctrct_abi = json.load(file_ctrct_abi)
    with open('./data/bin/'+ctrct_name+'.bin', 'r') as file_ctrct_bin:
        ctrct_byte = json.load(file_ctrct_bin)['object']
        if not ctrct_byte.startswith('0x'):
            ctrct_byte = '0x' + ctrct_byte
    # Create contract
    ctrct = w3.eth.contract(abi=ctrct_abi, bytecode=ctrct_byte)
    # Submit the transaction that deploys the contract
    tx_hash = ctrct.constructor().transact()
    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    # Instantiate contract
    ctrct = w3.eth.contract(address=tx_receipt.contractAddress, abi=ctrct_abi)
    log('Contract \"' + ctrct_name +'\" available at: ' + ctrct.address)
    with open("./data/contracts.txt", "a") as file_addresses:
        file_addresses.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', ' + ctrct_name + ', ' + ctrct.address + '\n')
        