import pytest
from brownie import accounts, WeddingRegistry
import brownie


def test_authority():
    authorities = accounts[0:3]

    registry_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})

    # check that only authorities can call updateAuthorities
    for acc in accounts:
        if acc in authorities:
            continue
        with brownie.reverts("Only authorized accounts can call this function"):
            registry_contract.updateAuthorities([acc], {"from": acc})

    # check that authorities can update authorities
    new_authorities = accounts[3:5]
    registry_contract.updateAuthorities(new_authorities, {"from": authorities[0]})

    # check that only new authorities can call updateAuthorities
    for acc in accounts:
        if acc in new_authorities:
            continue
        with brownie.reverts("Only authorized accounts can call this function"):
            registry_contract.updateAuthorities([acc], {"from": acc})

    # check that the set authorities are correct
    for acc in new_authorities:
        assert registry_contract.isAuthority(acc) == (acc in new_authorities)


def test_wedding_contract_initiation():
    authorities = accounts[0:3]
    fiances = accounts[3:5]

    registry_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})

    # check that initiateion fails if duplicate fiances are passed
    with brownie.reverts("Duplicate fiance addresses"):
        registry_contract.initiateWedding(
            [fiances[0], fiances[0], fiances[1]], 1923510554, {"from": fiances[0]}
        )

    # check that more than 1 fiance is not allowed
    with brownie.reverts("At least two fiances are required"):
        registry_contract.initiateWedding(
            [fiances[0], fiances[1], fiances[2]], 1923510554, {"from": fiances[0]}
        )

    # check that the wedding date is not in the past
    with brownie.reverts("Wedding date must be in the future"):
        registry_contract.initiateWedding(fiances, 0, {"from": fiances[0]})

    # finally create a valid wedding contract
    wedding_addr = registry_contract.initiateWedding(
        fiances, 1923510554, {"from": fiances[0]}
    )

    # TODO check that married fiances can not marry again
