from brownie import MyImplementation, MyProxy, Contract, accounts


def main():
    implementation_contract = MyImplementation.deploy({"from": accounts[0]})

    proxy_contract = MyProxy.deploy(
        implementation_contract.address, {"from": accounts[0]}
    )
    proxy_contract = Contract.from_abi(
        "MyImplementation", proxy_contract.address, MyImplementation.abi
    )

    proxy_contract.setValue(1, {"from": accounts[0]}).wait(1)
    proxy_contract.getValue({"from": accounts[0]})

    # proxy_contract_2 = MyProxy.deploy(
    #     implementation_contract.address, {"from": accounts[0]}
    # )
    # proxy_contract_2 = Contract.from_abi(
    #     "MyImplementation", proxy_contract_2.address, MyImplementation.abi
    # )

    # proxy_contract_2.setValue(2, {"from": accounts[0]})
    # print(proxy_contract_2.getValue({"from": accounts[0]}))
