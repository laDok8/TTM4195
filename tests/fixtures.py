import pytest
from brownie import WeddingRegistry, WeddingContract
import brownie


def create_registry_contract(authorities):
    wedding_implementation_contract = WeddingContract.deploy({"from": authorities[0]})
    registry_contract = WeddingRegistry.deploy(
        authorities, wedding_implementation_contract.address, {"from": authorities[0]}
    )
    return registry_contract


def add_succesfull_wedding(chain, registry_contract, fiances, wedding_date, guests):
    wedding_contract_addr = registry_contract.initiateWedding(
        fiances, wedding_date, {"from": fiances[0]}
    ).return_value
    wedding_contract = WeddingContract.at(wedding_contract_addr)

    for fiance in fiances:
        for guest in guests:
            wedding_contract.approveGuest(guest, {"from": fiance})

    ceremony_begin = (wedding_date // 86400) * 86400 + 36000
    chain.mine(timestamp=ceremony_begin)

    for fiance in fiances:
        wedding_contract.confirmWedding({"from": fiance}).wait(1)

    return wedding_contract


def add_pending_wedding(chain, registry_contract, fiances, wedding_date, guests):
    wedding_contract_addr = registry_contract.initiateWedding(
        fiances, wedding_date, {"from": fiances[0]}
    ).return_value
    wedding_contract = WeddingContract.at(wedding_contract_addr)

    for fiance in fiances:
        for guest in guests:
            wedding_contract.approveGuest(guest, {"from": fiance})

    ceremony_begin = (wedding_date // 86400) * 86400 + 36000
    chain.mine(timestamp=ceremony_begin)
    # only 1 of the fiance confirms the wedding
    wedding_contract.confirmWedding({"from": fiances[0]})

    return wedding_contract


def divorce_wedding(wedding_contract, divorcers):
    wedding_contract.divorce({"from": divorcers[0]})
    wedding_contract.divorce({"from": divorcers[1]})
