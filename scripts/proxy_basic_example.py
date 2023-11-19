from brownie import MyImplementation, MyProxy, Contract, accounts


def main():
    implementation_contract = MyImplementation.deploy({"from": accounts[0]})
    implementation_contract.setValue(3, {"from": accounts[0]}).wait(
        1
    )  # has mo effect on proxy state

    proxy_contract = MyProxy.deploy(
        implementation_contract.address, {"from": accounts[0]}
    )
    proxy_contract = Contract.from_abi(
        "MyImplementation", proxy_contract.address, MyImplementation.abi
    )

    proxy_contract.setValue(1, {"from": accounts[0]}).wait(1)
    implementation_contract.setValue(4, {"from": accounts[0]}).wait(
        1
    )  # has no effect on proxy state
    print(proxy_contract.getValue({"from": accounts[0]}))

    proxy_contract_2 = MyProxy.deploy(
        implementation_contract.address, {"from": accounts[0]}
    )
    proxy_contract_2 = Contract.from_abi(
        "MyImplementation", proxy_contract_2.address, MyImplementation.abi
    )

    proxy_contract_2.setValue(2, {"from": accounts[0]}).wait(1)
    implementation_contract.setValue(5, {"from": accounts[0]}).wait(
        1
    )  # has no effect on proxy state
    print(proxy_contract_2.getValue({"from": accounts[0]}))
