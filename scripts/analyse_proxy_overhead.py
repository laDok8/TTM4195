from brownie import MyProxy, MyImplementation, accounts, Contract, chain


def main():
    implementation_contract = MyImplementation.deploy({"from": accounts[0]})
    gas_usage_no_proxy = []
    for i in range(1, 100, 5):
        gas_usage_no_proxy.append(implementation_contract.executeLoop(i).gas_used)
        chain.mine(1)

    implementation_contract = MyImplementation.deploy({"from": accounts[0]})
    proxy_contract = MyProxy.deploy(implementation_contract, {"from": accounts[0]})
    proxy_contract = Contract.from_abi(
        "MyImplementation", proxy_contract.address, MyImplementation.abi
    )
    gas_usage_with_proxy = []
    for i in range(1, 100, 5):
        gas_usage_with_proxy.append(
            proxy_contract.executeLoop(i, {"from": accounts[0]}).gas_used
        )
        chain.mine(1)

    print("Gas usage without proxy: ", gas_usage_no_proxy)
    print("Gas usage with proxy:    ", gas_usage_with_proxy)
    overhead_absolut = [x - y for x, y in zip(gas_usage_with_proxy, gas_usage_no_proxy)]
    overhead_relative = [
        (x - y) / y * 100 for x, y in zip(gas_usage_with_proxy, gas_usage_no_proxy)
    ]
    print("Overhead absolut:        ", overhead_absolut)
    print("Overhead relative:       ", [round(x, 2) for x in overhead_relative])
