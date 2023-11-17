# Assignment 3 - Wedding Smart Contract

## Repo contents
This repository is structured as a brownie project. 
The `contracts` folder contains the smart contracts solidity code. 
The `scripts` folder contains scripts used to deploy the smart contracts and showcase their functionality.
The `tests` folder contains the tests for the smart contract.
Even though we used a brownie project in order to allow for easier testing, the smart contracts in the `contracts` folder can be deployed and tested using `Remix` as well.

## Design Description
Two distinct smart contracts are used in this project.
One is the `Wedding` contract, which contains the logic for the wedding procedure itself.
This includes the ability to initiate a wedding, revoke a wedding before the wedding date, invite and approve guests, let guests vote against the wedding, and finally, let the fiances agree to get married (and also get divorced afterward).
The other contract is the `WeddingRegistry`.
This contract is used to keep track of all the weddings that have been initiated and might get divorced.
This is done by using a so-called contract-factory pattern, where the `WeddingRegistry` contract is used to deploy new `Wedding` contracts.
This means that someone who wants to get married needs to call the `initiateWedding` function on the `WeddingRegistry` contract, which will then deploy a new `Wedding` contract.
Every step on the wedding procedure is then done on the `Wedding` contract, and only in the end, when the finances agree to get married, the `WeddingRegistry` contract gets called back by the `Wedding` contract to register the wedding.

The `WeddingRegistry` contract also issues ERC721 tokens for each wedding after the wedding has been registered.
The tokens are owned by the corresponding wedding contract and can be used to prove that a wedding has taken place.
The registry also tracks which address is a fiance in which wedding.
Therefore we can check whether a given address is a fiance in a wedding by simply checking if the address is associated with a wedding token.
Using OpenZeppelin's `ERC721` contract, it is very easy to implement this functionality and ensure unique, non-fungible tokens.
OpenZeppelin's `ERC721` contract also allows us to associate metadata with each token, which we use to store the wedding date and the names of the finances.
However, in favor of keeping sensitive data off-chain, we do not store any additional data on-chain.
Everything which should be relevant for a wedding registry is whether a person (or better, an address) is a fiance in a wedding or not.

The big downside of using the described factory-pattern is that for each wedding a new contract is deployed, which is very expensive.
This was solved by deploying `Proxy` contracts from the `WeddingRegistry` contract instead of `Wedding` contracts directly.
These `Proxy` contracts do not contain any wedding logic themselves, but instead forward all calls to a `Wedding`-Implementation contract.
Therefore we need to deploy the `Wedding`-Implementation contract only once, and then deploy a small and cheap `Proxy` contract for each wedding.
Using OpenZeppelin's `ERC1967Proxy` contract, this can be done in a very simple way without having to write its own `Proxy` contract.

Using this Contract-factory pattern together with the `ERC1967Proxy` contract has some significant advantages:
- The `Wedding`-Implementation contract can be upgraded without having to redeploy the registry. This can be extremely helpful if the "laws" for getting married change or if a bug is found in the implementation. An authority can simply update the address of the `Wedding`-Implementation contract in the registry, and all future weddings will use the new implementation.
- We achieve a nice separation of concerns. The `WeddingRegistry` contract is only responsible for keeping track of all weddings, while the `Wedding`-Implementation contract is only responsible for the wedding logic. This makes the code easier to read and understand.
- The overhead of deploying a new contract for each wedding is reduced to a minimum since the `Proxy` contracts are very small and cheap to deploy. Also we do not need expensive lookups for all relevant data in the `WeddingRegistry` contract as all weddings have their 'own' contract.

## Brownie project setup
In order to run the test suite and scripts, you need to set up this repository as a brownie project.
To do so, you need to install `brownie` and `ganache-cli`.
Note that `brownie` requires python 3.9, so it is recommended to use a virtual conda environment for simply changing the python version.
```bash
conda create -n wedding_env python=3.9
conda activate wedding_env
```
Then you install the required packages.
```bash
pip install eth-brownie
npm install -g ganache-cli
```
Then, you need to clone this repository and cd into it and install the OpenZeppelin contracts.
```bash
git clone
cd TTM4195
npm install .
```
Finally, you need to initialize the brownie project.
```bash
brownie init -f
```
Then you can run the tests and scripts using the brownie command.
```bash
brownie test
brownie run scripts/<script_name>.py
```