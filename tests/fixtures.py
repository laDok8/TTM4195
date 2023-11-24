from typing import List

import pytest
from brownie import WeddingRegistry, WeddingContract
import brownie

DAY_IN_SECONDS = 600
START_TO_VOTE_SECONDS = 120


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

    ceremony_begin = (
        wedding_date // DAY_IN_SECONDS
    ) * DAY_IN_SECONDS + START_TO_VOTE_SECONDS
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

    ceremony_begin = (
        wedding_date // DAY_IN_SECONDS
    ) * DAY_IN_SECONDS + START_TO_VOTE_SECONDS
    chain.mine(timestamp=ceremony_begin)
    # only 1 of the fiance confirms the wedding
    wedding_contract.confirmWedding({"from": fiances[0]})

    return wedding_contract


def add_pending_wedding_non_approved_guests(
    chain, registry_contract, fiances, wedding_date, guests
):
    wedding_contract_addr = registry_contract.initiateWedding(
        fiances, wedding_date, {"from": fiances[0]}
    ).return_value
    wedding_contract = WeddingContract.at(wedding_contract_addr)

    ceremony_begin = (
        wedding_date // DAY_IN_SECONDS
    ) * DAY_IN_SECONDS + START_TO_VOTE_SECONDS
    chain.mine(timestamp=ceremony_begin)
    # only 1 of the fiance confirms the wedding
    wedding_contract.confirmWedding({"from": fiances[0]})

    return wedding_contract


def add_parallel_pending_weddings(
    chain, registry_contract, fiances_list: List[List], wedding_date
):
    wedding_contracts = []
    for fiances in fiances_list:
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)
        wedding_contracts.append(wedding_contract)

    ceremony_begin = (
        wedding_date // DAY_IN_SECONDS
    ) * DAY_IN_SECONDS + START_TO_VOTE_SECONDS
    chain.mine(timestamp=ceremony_begin)
    # only 1 of the fiance confirms the wedding
    for wedding_contract, fiances in zip(wedding_contracts, fiances_list):
        wedding_contract.confirmWedding({"from": fiances[0]})

    return wedding_contracts


def divorce_wedding(wedding_contract, divorcers):
    wedding_contract.divorce({"from": divorcers[0]})
    wedding_contract.divorce({"from": divorcers[1]})
