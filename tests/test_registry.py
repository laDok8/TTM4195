import pytest
from brownie import WeddingRegistry
import brownie


# @pytest.fixture
# def registry_contract(accounts):
#     authorities = accounts[0:3]
#     reg_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})
#     return reg_contract, authorities
def create_registry_contract(authorities):
    registry_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})
    return registry_contract


def add_succesfull_wedding(registry_contract, fiances, wedding_date, guests):
    wedding_contract = registry_contract.initiateWedding(
        fiances, wedding_date, {"from": fiances[0]}
    )
    wedding_contract.inviteGuests(guests, {"from": fiances[0]})
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
    def test_wedding_contract_initiation(self, accounts):
        authorities = accounts[0:3]
        fiances = accounts[3:5]

        registry_contract = WeddingRegistry.deploy(
            authorities, {"from": authorities[0]}
        )

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
