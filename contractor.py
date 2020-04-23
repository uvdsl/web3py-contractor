import argparse
from web3 import Web3, HTTPProvider, WebsocketProvider
from solcx import compile_source, install_solc, set_solc_version, get_installed_solc_versions
from vyper import compile_code
from datetime import datetime
import json


def log(message):
    print('==', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '==', message)


DEFAULT_CONNECTION = 'ws://localhost:8546'
provider = WebsocketProvider(DEFAULT_CONNECTION) # default

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", help="Geth connection endpoint, default: {}".format(DEFAULT_CONNECTION))
parser.add_argument("contract", help="Contract file in ./data/src, e.g. myContract.sol or myContract.vy. If you don't provide onyle the name without {.type} the contractor will assume abi and bin files to be in place.")
args = parser.parse_args()

if args.endpoint:
    if args.endpoint.startswith('http://'):
        provider = HTTPProvider(args.endpoint)
    elif args.endpoint.startswith('ws://'):
        provider = WebsocketProvider(args.endpoint)
    else:
        log("What is this endpoint? Falling back to default ... ")
log(provider)

contract_name = args.contract.partition('.')[0]
contract_lang = args.contract.partition('.')[2]

########################
### COMPILE CONTRACT ###
########################

if contract_lang == '':
    log('Skipping compilation.')
else: 
    # read in
    with open('./data/src/' + args.contract, 'r') as file_ctrct_src:
        ctrct_src = file_ctrct_src.read()
    # VYPER
    if contract_lang == 'vy':
        log('Compiling vyper contract!')
        abi = 'abi'
        byte = 'bytecode'
        # compile
        compiled_contract = compile_code(ctrct_src, [abi, byte])
        # done
        log('Done compiling vyper contract.')
    # SOLIDITY
    elif contract_lang == 'sol':
        solc_version = "v" + ctrct_src.partition(' ^')[2].partition(';\n')[0]
        # version
        if not solc_version in get_installed_solc_versions():
            log("Installing solc {}".format(solc_version))
            install_solc(solc_version)
            log("Done.")
        set_solc_version(solc_version)
        # compile
        log('Compiling solidity {} contract!'.format(solc_version))
        abi = 'abi'
        byte = 'bin'
        compiled_contract = compile_source(ctrct_src, output_values=[abi, byte])
        # done
        log('Done compiling solidity contract.')
        compiled_contract = compiled_contract['<stdin>:{}'.format(contract_name)]
    # write
    with open("./data/abi/{}.abi".format(contract_name), "w") as file_abi:
        json.dump(compiled_contract[abi], file_abi)
    with open("./data/bin/{}.bin".format(contract_name), "w") as file_bin:
        file_bin.write(compiled_contract[byte])

#######################
### DEPLOY CONTRACT ###
#######################

try:
    log('Connecting to Geth ...')
    w3 = Web3(provider)
    log('Connected at block: {}'.format(w3.eth.blockNumber))
except:
    log('Did not reach Geth at ...')
else:
    
    # Read abi and bin
    with open('./data/abi/{}.abi'.format(contract_name), 'r') as file_ctrct_abi:
        ctrct_abi = json.load(file_ctrct_abi)
    with open('./data/bin/{}.bin'.format(contract_name), 'r') as file_ctrct_bin:
        ctrct_byte = file_ctrct_bin.read()
        if not ctrct_byte.startswith('0x'):
            ctrct_byte = '0x' + ctrct_byte
    # Create contract
    ctrct = w3.eth.contract(abi=ctrct_abi, bytecode=ctrct_byte)

    # Display account to use
    w3.eth.defaultAccount = w3.eth.accounts[0]
    log('Account: ' + w3.eth.defaultAccount)
    # Read in passphrase
    passphrase = input('== ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' == Passphrase: ')
    log('Unlock: ' + str(w3.geth.personal.unlockAccount(w3.eth.defaultAccount, passphrase)))
    
    # Submit the transaction that deploys the contract
    tx_hash = ctrct.constructor().transact()
    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    # Instantiate contract
    ctrct = w3.eth.contract(address=tx_receipt.contractAddress, abi=ctrct_abi)
    log('Contract \"' + contract_name +'\" available at: ' + ctrct.address)
    with open("./data/contracts.txt", "a") as file_addresses:
        file_addresses.write('{}, {}, {}, {}\n'.format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            contract_name,
            ctrct.address, 
            provider)
        )