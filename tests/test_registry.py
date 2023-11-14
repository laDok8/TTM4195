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
