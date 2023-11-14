from brownie import WeddingRegistry, accounts


def main():
    deployer = accounts[0]
    WeddingRegistry.deploy([], {"from": deployer})
