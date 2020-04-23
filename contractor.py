import argparse
from getpass import getpass
from web3 import Web3, HTTPProvider, WebsocketProvider
from solcx import compile_source, install_solc, set_solc_version, get_installed_solc_versions
from vyper import compile_code
from datetime import datetime
import json
import sys


def log(message):
    print('==', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '==', message)


parser = argparse.ArgumentParser()
p_group_deploy = parser.add_argument_group('deployment arguments')
p_group_deploy.add_argument("-e", "--endpoint", help="Geth connection endpoint. If you don't provide an endpoint, deployment will be skipped.")
p_group_deploy.add_argument("-a", "--account", help="Account to unlock in 0x format. If you don't provide an account, available accounts will be suggested.")
p_group_deploy.add_argument("-p", "--password", help="The password to unlock the given account. If you don't provide a password, you will be prompted.")
parser.add_argument("contract", help="Contract file in ./data/src, e.g. myContract.sol or myContract.vy, to be compiled. If the filetype is not .vy or .sol, compilation will be skipped")
args = parser.parse_args()

########################
### COMPILE CONTRACT ###
########################

contract_name = args.contract.partition('.')[0]
contract_lang = args.contract.partition('.')[2]

if not (contract_lang == 'vy' or contract_lang == 'sol'):
    log('Did not recognize Vyper or Solidity file!')
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

if not args.endpoint:
    log('Skipping deployment.')
    sys.exit(0)

if args.endpoint.startswith('http://'):
    provider = HTTPProvider(args.endpoint)
elif args.endpoint.startswith('ws://'):
    provider = WebsocketProvider(args.endpoint)

log(provider)


# Read abi and bin
with open('./data/abi/{}.abi'.format(contract_name), 'r') as file_ctrct_abi:
    ctrct_abi = json.load(file_ctrct_abi)
with open('./data/bin/{}.bin'.format(contract_name), 'r') as file_ctrct_bin:
    ctrct_byte = file_ctrct_bin.read()
    if not ctrct_byte.startswith('0x'):
        ctrct_byte = '0x' + ctrct_byte

try:
    log('Connecting to Geth ...')
    w3 = Web3(provider)
    log('Connected at block: {}'.format(w3.eth.blockNumber))
except:
    log('Did not reach Geth at ...')
else:
    # Create contract
    ctrct = w3.eth.contract(abi=ctrct_abi, bytecode=ctrct_byte)

    # Wallet
    if not args.account:
        log('Available Accounts:')
        for index, account in enumerate(w3.eth.accounts):
            print('\t[{}] {}'.format(index, account))
        idx = int(input('== ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' == Account Index to use: '))
        args.account = w3.eth.accounts[idx]
    w3.eth.defaultAccount = args.account
    log('Account: ' + w3.eth.defaultAccount)
    # Password
    if not args.password:
        # Read in password
        args.password = getpass('== ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' == Passphrase: ')
    log('Unlock: {}'.format(w3.geth.personal.unlockAccount(w3.eth.defaultAccount, args.password)))
            
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