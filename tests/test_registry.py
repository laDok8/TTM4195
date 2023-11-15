import pytest
from brownie import WeddingRegistry, WeddingContract
import brownie


def create_registry_contract(authorities):
    registry_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})
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


class TestAuthority:
    def test_isAuthority(self, accounts):
        authorities = accounts[0:3]
        registry_contract = create_registry_contract(authorities)
        for acc in accounts:
            assert registry_contract.isAuthority(acc) == (acc in authorities)

    def test_only_authority_can_call_UpdateAuthorities(self, accounts):
        authorities = accounts[0:3]
        registry_contract = create_registry_contract(authorities)

        for acc in accounts:
            if acc in authorities:
                continue
            with brownie.reverts("Only authorized accounts can call this function"):
                registry_contract.updateAuthorities([acc], {"from": acc})

    def test_updateAuthorities(self, accounts):
        authorities = accounts[0:3]
        registry_contract = create_registry_contract(authorities)

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


class TestInitiateWedding:
    def test_initiateWedding_no_duplicates(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        with brownie.reverts("Duplicate fiance addresses"):
            registry_contract.initiateWedding(
                [accounts[4], accounts[5], accounts[4]],
                chain.time() + 86400,
                {"from": accounts[4]},
            )

    def test_initiateWedding_min_fiances(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        with brownie.reverts("At least two fiances are required"):
            registry_contract.initiateWedding(
                [accounts[4]], chain.time() + 86400, {"from": accounts[0]}
            )

    def test_initiateWedding_future_date(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        with brownie.reverts("Wedding date must be at least on the next day"):
            registry_contract.initiateWedding(
                accounts[4:7], chain.time(), {"from": accounts[4]}
            )

    def test_initiateWedding_all_fiances_are_unmarried(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + 86400, []
        )

        with brownie.reverts("One of the fiances is already married"):
            registry_contract.initiateWedding(
                [accounts[4], accounts[7], accounts[8]],
                chain.time() + 86400,
                {"from": accounts[4]},
            )
