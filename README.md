# Contractor (web3py) 

A contract compilation and deployment script, written in python using the web3py Websocket or RPC interface for geth.

## Requirements
I used a conda environment with python 3.7:
```
pip install -r requirements.txt
```

## Usage
```
usage: contractor.py [-h] [-e ENDPOINT] [-cargs CONSTRUCTOR_ARGS] [-a ACCOUNT] [-p PASSWORD] contract

positional arguments:
  contract              Contract file in ./data/src/, e.g. myContract.sol or
                        myContract.vy, to be compiled. If the filetype is not
                        .vy or .sol, compilation will be skipped.

optional arguments:
  -h, --help            show this help message and exit

deployment arguments:
  -e ENDPOINT, --endpoint ENDPOINT
                        Geth connection endpoint. If you don't provide an
                        endpoint, deployment will be skipped.
 -cargs CONSTRUCTOR_ARGS, --constructor_args CONSTRUCTOR_ARGS
                        Arguments of the contract constructor in array syntax,
                        i.e. [args1,args2,...]. If the contract constructor
                        requires arguments you didn't provide, the deployment
                        will fail.
  -a ACCOUNT, --account ACCOUNT
                        Account to unlock in 0x format. If you don't provide
                        an account, available accounts will be suggested.
  -p PASSWORD, --password PASSWORD
                        The password to unlock the given account. If you don't
                        provide a password, you will be prompted.
```
