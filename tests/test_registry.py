import pytest
import brownie
from brownie import WeddingRegistry, WeddingContract

from fixtures import (
    create_registry_contract,
    add_succesfull_wedding,
    add_pending_wedding,
    divorce_wedding,
    add_parallel_pending_weddings,
)

DAY_IN_SECONDS = 600
START_TO_VOTE_SECONDS = 120


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

    def test_event_emitted_on_updateAuthorities(self, accounts):
        authorities = accounts[0:3]
        registry_contract = create_registry_contract(authorities)

        new_authorities = accounts[3:5]
        tx = registry_contract.updateAuthorities(
            new_authorities, {"from": authorities[0]}
        )
        emmitted_event = tx.events["AuthoritiesUpdated"]
        assert emmitted_event["authorities"] == new_authorities


class TestInitiateWedding:
    def test_initiateWedding_no_duplicates(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        with brownie.reverts("Duplicate fiance addresses"):
            registry_contract.initiateWedding(
                [accounts[4], accounts[5], accounts[4]],
                chain.time() + DAY_IN_SECONDS,
                {"from": accounts[4]},
            )

    def test_initiateWedding_min_fiances(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        with brownie.reverts("At least two fiances are required"):
            registry_contract.initiateWedding(
                [accounts[4]], chain.time() + DAY_IN_SECONDS, {"from": accounts[0]}
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
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        with brownie.reverts("One of the fiances is already married"):
            registry_contract.initiateWedding(
                [accounts[4], accounts[7], accounts[8]],
                chain.time() + DAY_IN_SECONDS,
                {"from": accounts[4]},
            )

    def test_initiateWedding_callable_after_divorce(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        chain.mine(timestamp=chain.time() + DAY_IN_SECONDS)
        wedding_contract.divorce({"from": accounts[4]})
        wedding_contract.divorce({"from": accounts[5]})

        registry_contract.initiateWedding(
            [accounts[4], accounts[7]],
            chain.time() + DAY_IN_SECONDS,
            {"from": accounts[4]},
        )

    def test_event_emitted_on_initiateWedding(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        wedding_date = chain.time() + DAY_IN_SECONDS
        tx = registry_contract.initiateWedding(
            accounts[4:6], wedding_date, {"from": accounts[4]}
        )
        emmitted_event = tx.events["WeddingInitiated"]
        assert emmitted_event["fiances"] == accounts[4:6]
        assert emmitted_event["weddingDate"] == wedding_date
        assert emmitted_event["weddingContractAddress"] == tx.return_value


class TestParallelWeddingScenarios:
    def test_parallel_weddings_with_distinct_fiances(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contracts = add_parallel_pending_weddings(
            chain,
            registry_contract,
            [accounts[4:6], accounts[7:9]],
            chain.time() + DAY_IN_SECONDS,
        )

        for acc in accounts[4:9]:
            with brownie.reverts("Only married accounts can call this function"):
                registry_contract.getMyWeddingTokenId({"from": acc})

        # final fiances confirm their weddings
        wedding_contracts[0].confirmWedding({"from": accounts[5]})
        wedding_contracts[1].confirmWedding({"from": accounts[8]})

        for acc in accounts[4:6]:
            assert registry_contract.getMyWeddingTokenId({"from": acc}) == 0
        for acc in accounts[7:9]:
            assert registry_contract.getMyWeddingTokenId({"from": acc}) == 1

    def test_parallel_weddings_same_fiances_slower_confirm_is_invalid(
        self, chain, accounts
    ):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contracts = add_parallel_pending_weddings(
            chain,
            registry_contract,
            [accounts[4:6], accounts[4:6]],
            chain.time() + DAY_IN_SECONDS,
        )

        # first wedding is finalized
        wedding_contracts[0].confirmWedding({"from": accounts[5]})

        # second wedding can not be finalized
        with brownie.reverts("One of the fiances is already married"):
            wedding_contracts[1].confirmWedding({"from": accounts[5]})

        assert registry_contract.getMyWeddingTokenId({"from": accounts[4]}) == 0

    def test_parralel_weddings_overlapping_fiances_slower_confirm_is_invalid(
        self, chain, accounts
    ):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contracts = add_parallel_pending_weddings(
            chain,
            registry_contract,
            [accounts[4:6], accounts[5:7]],
            chain.time() + DAY_IN_SECONDS,
        )

        # first wedding is finalized
        wedding_contracts[0].confirmWedding({"from": accounts[5]})
        assert registry_contract.getMyWeddingTokenId({"from": accounts[4]}) == 0
        assert registry_contract.getMyWeddingTokenId({"from": accounts[5]}) == 0

        # second wedding can not be finalized
        with brownie.reverts("One of the fiances is already married"):
            wedding_contracts[1].confirmWedding({"from": accounts[6]})

        with brownie.reverts("Only married accounts can call this function"):
            registry_contract.getMyWeddingTokenId({"from": accounts[6]})

    def test_parallel_weddings_with_divorce(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_date_1 = chain.time() + DAY_IN_SECONDS
        wedding_date_2 = chain.time() + 2 * DAY_IN_SECONDS
        wedding_date_2_start = wedding_date_2 - (wedding_date_2 % DAY_IN_SECONDS)

        # add pending wedding for next day
        wedding_contract_1 = WeddingContract.at(
            registry_contract.initiateWedding(
                accounts[4:6], wedding_date_1, {"from": accounts[4]}
            ).return_value
        )
        # add other pending wedding with overlapping fiances the day after
        wedding_contract_2 = WeddingContract.at(
            registry_contract.initiateWedding(
                accounts[5:7], wedding_date_2, {"from": accounts[5]}
            ).return_value
        )

        # finalize the first wedding
        chain.mine(timestamp=wedding_date_1 + START_TO_VOTE_SECONDS + 1)
        wedding_contract_1.confirmWedding({"from": accounts[5]})
        wedding_contract_1.confirmWedding({"from": accounts[4]})

        # divorce the first wedding right after the wedding date
        chain.mine(timestamp=wedding_date_2_start + 100)
        divorce_wedding(wedding_contract_1, accounts[4:6])

        # finalize the second wedding -> should be possible agsin
        chain.mine(timestamp=wedding_date_2_start + START_TO_VOTE_SECONDS + 1)
        wedding_contract_2.confirmWedding({"from": accounts[5]})
        wedding_contract_2.confirmWedding({"from": accounts[6]})

        # check that the first wedding is not registered anymore
        with brownie.reverts("Only married accounts can call this function"):
            registry_contract.getMyWeddingTokenId({"from": accounts[4]})

        # check that the second wedding is registered
        # after a wedding got divroced the tokenId is also available again !!!
        assert registry_contract.getMyWeddingTokenId({"from": accounts[5]}) == 1
        assert registry_contract.getMyWeddingTokenId({"from": accounts[6]}) == 1

        # assert that the list of fiances are correct
        assert (
            wedding_contract_2.getMyPartnersAddresses({"from": accounts[5]})
            == accounts[5:7]
        )


class TestGetWeddingTokenId:
    def test_getMyWeddingTokenId_only_callable_by_fiance(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts:
            if acc in accounts[4:6]:
                assert registry_contract.getMyWeddingTokenId({"from": acc}) == 0
            else:
                with brownie.reverts("Only married accounts can call this function"):
                    registry_contract.getMyWeddingTokenId({"from": acc})

    def test_getMyWeddingTokeId_not_callable_after_burn(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )
        chain.mine(timestamp=chain.time() + DAY_IN_SECONDS)
        divorce_wedding(wedding_contract, accounts[4:6])

        for acc in accounts[4:6]:
            with brownie.reverts("Only married accounts can call this function"):
                registry_contract.getMyWeddingTokenId({"from": acc})

    def test_getMyWeddingTokenId_only_callable_after_issue(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        add_pending_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts:
            with brownie.reverts("Only married accounts can call this function"):
                registry_contract.getMyWeddingTokenId({"from": acc})

    def test_getMyWeddingTokenId_returns_correct_token_id(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        fiances_1 = accounts[4:6]
        add_succesfull_wedding(
            chain, registry_contract, fiances_1, chain.time() + DAY_IN_SECONDS, []
        )
        for fi in fiances_1:
            assert registry_contract.getMyWeddingTokenId({"from": fi}) == 0

        fiances_2 = accounts[7:9]
        add_succesfull_wedding(
            chain, registry_contract, fiances_2, chain.time() + DAY_IN_SECONDS, []
        )
        for fi in fiances_2:
            assert registry_contract.getMyWeddingTokenId({"from": fi}) == 1

    def test_getMyWeddingTokenId_after_divorce(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:1])
        wedding_contract_1 = add_succesfull_wedding(
            chain, registry_contract, accounts[1:3], chain.time() + DAY_IN_SECONDS, []
        )
        wedding_contract_2 = add_succesfull_wedding(
            chain, registry_contract, accounts[3:5], chain.time() + DAY_IN_SECONDS, []
        )
        wedding_contract_3 = add_succesfull_wedding(
            chain, registry_contract, accounts[5:7], chain.time() + DAY_IN_SECONDS, []
        )

        assert registry_contract.getMyWeddingTokenId({"from": accounts[1]}) == 0
        assert registry_contract.getMyWeddingTokenId({"from": accounts[3]}) == 1
        assert registry_contract.getMyWeddingTokenId({"from": accounts[5]}) == 2

        chain.mine(timestamp=chain.time() + DAY_IN_SECONDS)
        divorce_wedding(wedding_contract_2, accounts[3:5])

        for acc in accounts[3:5]:
            with brownie.reverts("Only married accounts can call this function"):
                registry_contract.getMyWeddingTokenId({"from": acc})

        wedding_contract_4 = add_succesfull_wedding(
            chain, registry_contract, accounts[7:9], chain.time() + DAY_IN_SECONDS, []
        )
        assert registry_contract.getMyWeddingTokenId({"from": accounts[7]}) == 3


class TestGetWeddingContractAddress:
    def test_getMyWeddingContractAddress_only_callable_by_fiance(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts:
            if acc in accounts[4:6]:
                assert (
                    registry_contract.getMyWeddingContractAddress({"from": acc})
                    == wedding_contract.address
                )
            else:
                with brownie.reverts("Only married accounts can call this function"):
                    registry_contract.getMyWeddingContractAddress({"from": acc})

    def test_getMyWeddingContractAddress_not_callable_after_burn(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )
        chain.mine(timestamp=chain.time() + DAY_IN_SECONDS)
        divorce_wedding(wedding_contract, accounts[4:6])

        for acc in accounts[4:6]:
            with brownie.reverts("Only married accounts can call this function"):
                registry_contract.getMyWeddingContractAddress({"from": acc})

    def test_getMyWeddingContractAddress_only_callable_after_issue(
        self, chain, accounts
    ):
        registry_contract = create_registry_contract(accounts[0:3])
        add_pending_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts:
            with brownie.reverts("Only married accounts can call this function"):
                registry_contract.getMyWeddingContractAddress({"from": acc})

    def test_getMyWeddingContractAddress_returns_correct_address(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:3])

        fiances_1 = accounts[4:6]
        wedding_contract_1 = add_succesfull_wedding(
            chain, registry_contract, fiances_1, chain.time() + DAY_IN_SECONDS, []
        )
        for fi in fiances_1:
            assert (
                registry_contract.getMyWeddingContractAddress({"from": fi})
                == wedding_contract_1.address
            )

        fiances_2 = accounts[7:9]
        wedding_contract_2 = add_succesfull_wedding(
            chain, registry_contract, fiances_2, chain.time() + DAY_IN_SECONDS, []
        )
        for fi in fiances_2:
            assert (
                registry_contract.getMyWeddingContractAddress({"from": fi})
                == wedding_contract_2.address
            )


class TestDeployedContractModifiers:
    def test_issueWeddingCertificate_only_callable_by_wedding_contract(
        self, chain, accounts
    ):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contract = add_pending_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts:
            with brownie.reverts(
                "Only deployed wedding contracts can call this function"
            ):
                registry_contract.issueWeddingCertificate(accounts[4:6], {"from": acc})

        #  this is not possible on a "normal" blockchain as we can not emulate the sender
        registry_contract.issueWeddingCertificate(
            accounts[4:6], {"from": wedding_contract}
        )

    def test_burnWeddingCertificate_only_callable_by_wedding_contract(
        self, chain, accounts
    ):
        registry_contract = create_registry_contract(accounts[0:3])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts:
            with brownie.reverts(
                "Only deployed wedding contracts can call this function"
            ):
                registry_contract.burnWeddingCertificate({"from": acc})

        registry_contract.burnWeddingCertificate({"from": wedding_contract})


# class TestTokenURI:
#     def test_tokenURI_retreival(self, chain, accounts):
#         registry_contract = create_registry_contract(accounts[0:3])
#         wedding_contract = add_succesfull_wedding(
#             chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
#         )

#         token_id = registry_contract.getMyWeddingTokenId({"from": accounts[4]})
#         assert (
#             registry_contract.tokenURI(token_id, {"from": accounts[4]})
#             == "Here we can add arbitrary data to the token. For example a link to some off chain data."
#         )

#     def test_tokenURI_onyl_callable_by_corresponding_fiances(self, chain, accounts):
#         registry_contract = create_registry_contract(accounts[0:3])
#         wedding_contract = add_succesfull_wedding(
#             chain, registry_contract, accounts[4:6], chain.time() + DAY_IN_SECONDS, []
#         )

#         token_id = registry_contract.getMyWeddingTokenId({"from": accounts[4]})
#         for acc in accounts:
#             if acc in accounts[4:6]:
#                 assert (
#                     registry_contract.tokenURI(token_id, {"from": acc})
#                     == "Here we can add arbitrary data to the token. For example a link to some off chain data."
#                 )
#             else:
#                 with brownie.reverts(
#                     "Only fiances of the wedding contract can call this function"
#                 ):
#                     registry_contract.tokenURI(token_id, {"from": acc})
