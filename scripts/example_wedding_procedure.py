from brownie import WeddingRegistry, accounts


def main():
    authorities = accounts[0:3]
    fiances = accounts[3:5]
    guests = accounts[5:8]
    unrelated = accounts[8:10]

    registry_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})
