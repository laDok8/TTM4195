import pytest
import brownie

from brownie import WeddingRegistry, WeddingContract


from fixtures import (
    create_registry_contract,
    add_succesfull_wedding,
    add_pending_wedding,
    divorce_wedding,
)


class TestRevokeEngagement:
    def test_no_functions_callable_after_revoke(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        # one fiance revokes the wedding directly after it was initiated
        wedding_contract.revokeEngagement({"from": fiances[0]})

        # The wedding got revoked by fiances[0], check that no functions from the wedding contract are callable anymore
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.approveGuest(guests[0], {"from": fiances[0]})

    def test_revoke_only_callable_before_wedding(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        # timetravel to wedding day
        chain.mine(timestamp=wedding_date)

        # the wedding should not be revokable anymore, because it's already the wedding day
        with brownie.reverts("Action can only be performed before the wedding day"):
            wedding_contract.revokeEngagement({"from": fiances[0]})

    def test_revoke_only_callable_by_fiances(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        # the wedding should only be revokable by fiances
        with brownie.reverts("Only fiances can call this function"):
            wedding_contract.revokeEngagement({"from": authorities[0]})
        with brownie.reverts("Only fiances can call this function"):
            wedding_contract.revokeEngagement({"from": guests[0]})
        with brownie.reverts("Only fiances can call this function"):
            wedding_contract.revokeEngagement({"from": unknowns[0]})

    def test_revoke_only_callable_once(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        # one fiance revokes the wedding directly after it was initiated
        wedding_contract.revokeEngagement({"from": fiances[0]})

        # the revoke function should not be callable a second time
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.revokeEngagement({"from": fiances[0]})
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.revokeEngagement({"from": fiances[1]})

    def test_event_sent_after_revoke(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        # one fiance revokes the wedding directly after it was initiated
        tx = wedding_contract.revokeEngagement({"from": fiances[0]})

        # a wedding event should've been emitted
        assert "weddingCanceled" in tx.events


class TestApproveGuests:
    def test_only_callable_by_fiances(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        # only fiances should be allowed to approve guests
        with brownie.reverts("Only fiances can call this function"):
            wedding_contract.approveGuest(guests[0], {"from": authorities[0]})
        with brownie.reverts("Only fiances can call this function"):
            wedding_contract.approveGuest(guests[0], {"from": guests[0]})
        with brownie.reverts("Only fiances can call this function"):
            wedding_contract.approveGuest(guests[0], {"from": unknowns[0]})

    def test_only_callable_before_wedding(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        # timetravel to wedding day
        chain.mine(timestamp=wedding_date)

        # guests cannot be added anymore, because it's already the wedding day
        with brownie.reverts("Action can only be performed before the wedding day"):
            wedding_contract.approveGuest(guests[0], {"from": fiances[0]})

    def test_only_callable_when_not_cancelled(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        wedding_date = chain.time() + 86400

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        # one fiance revokes the wedding directly after it was initiated
        wedding_contract.revokeEngagement({"from": fiances[0]})

        # guests cannot be added anymore, because the wedding is revoked
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.approveGuest(guests[0], {"from": fiances[0]})

    def test_approved_guest_can_vote(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400
        start_of_wedding_day = wedding_date - (wedding_date % 86400);

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        # timetravel to wedding day
        chain.mine(timestamp=start_of_wedding_day)

        # approved guests can vote
        tx = wedding_contract.voteAgainstWedding({"from": guests[0]})
        assert "voteAgainstWeddingOccured" in tx.events

    def test_guest_not_approved_if_not_all_fiances_approved(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400
        start_of_wedding_day = wedding_date - (wedding_date % 86400);

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        # not all fiances approve guest
        for fiance in fiances[:-1]:
            wedding_contract.approveGuest(guests[0], {"from": fiance})

        # timetravel to wedding day
        chain.mine(timestamp=start_of_wedding_day)

        # guest can only vote if all fiances approved the guest
        with brownie.reverts("Only guests with voting right can call this function"):
            wedding_contract.voteAgainstWedding({"from": guests[0]})

    def test_guest_can_only_be_approved_once(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400
        start_of_wedding_day = wedding_date - (wedding_date % 86400);

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)


        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance})

        with brownie.reverts("Guest is already approved"):
            wedding_contract.approveGuest(guests[0], {"from": fiances[0]})

    def test_invitation_event_sent_after_final_approve(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + 86400
        start_of_wedding_day = wedding_date - (wedding_date % 86400);

        registry_contract = create_registry_contract(authorities)
        wedding_contract_addr = registry_contract.initiateWedding(
            fiances, wedding_date, {"from": fiances[0]}
        ).return_value
        wedding_contract = WeddingContract.at(wedding_contract_addr)

        for fiance in fiances[:-1]:
            wedding_contract.approveGuest(guests[0], {"from": fiance})

        # invitation event is sent after last approval
        tx = wedding_contract.approveGuest(guests[0], {"from": fiances[-1]})
        assert "inviteSent" in tx.events


class TestVoteAgainstWedding:
    def test_onyl_callable_on_wedding_day_before_deadline(self):
        pass

    def test_onyl_callable_by_approved_guest(self):
        pass

    def test_only_callable_once_per_guest(self):
        pass

    def test_only_callable_if_not_cancelled(self):
        pass

    def test_no_approved_guests(self):
        pass

    def test_event_sent_after_vote(self):
        pass

    def test_event_sent_after_cancel(self):
        pass

    @pytest.mark.parametrize("m, n", [(0, 0), (0, 1), (1, 3), (2, 3), (3, 3)])
    def test_n_out_of_m_guests_voted_against(self, m, n):
        pass


class TestConfirmWedding:
    def test_only_callable_by_fiances(self):
        pass

    def test_onyl_callable_on_wedding_day_after_voting_deadline(self):
        pass

    def test_only_callable_if_not_cancelled(self):
        pass

    def test_double_confirm_does_not_change_anything(self):
        pass

    def test_wedding_certificate_issued_after_final_confirm(self):
        pass

    def test_no_certificate_issued_if_not_all_fiances_confirmed(self):
        pass

    def test_event_emitted_after_each_confirm(self):
        pass

    def test_event_emitted_after_final_confirm(self):
        pass


class TestDivorce:
    def test_only_callable_after_wedding_day(self):
        pass

    def test_only_callable_if_not_cancelled(self):
        pass

    def test_only_callable_by_fiances_or_authorities(self):
        pass

    def test_divorce_by_2_spouses(self):
        pass

    def test_divorce_by_1_spouse_and_1_authority(self):
        pass

    def test_divorce_fails_if_2_authorities(self):
        pass

    def test_divorce_can_only_be_called_once_per_fiance(self):
        pass

    def test_initiate_wedding_possible_after_divorce(self):
        pass

    def test_event_emitted_after_divorce_initiated(self):
        pass

    def test_event_emitted_after_successful_divorce(self):
        pass


class TestGetMyPartners:
    def test_getMyPartners_only_callable_by_fiances(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[2:6], chain.time() + 86400, []
        )

        for acc in accounts:
            if acc in accounts[2:6]:
                assert (
                    wedding_contract.getMyPartnersAddresses({"from": acc})
                    == accounts[2:6]
                )
            else:
                with brownie.reverts("Only fiances can call this function"):
                    wedding_contract.getMyPartnersAddresses({"from": acc})

    def test_getMyPartners_not_callable_after_divorce(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[2:6], chain.time() + 86400, []
        )

        chain.mine(timestamp=chain.time() + 86400)
        divorce_wedding(wedding_contract, accounts[2:4])

        for acc in accounts[2:4]:
            with brownie.reverts("The wedding has been canceled"):
                wedding_contract.getMyPartnersAddresses({"from": acc})

    def test_getMyPartners_not_callable_after_revoke(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = WeddingContract.at(
            registry_contract.initiateWedding(
                accounts[2:6], chain.time() + 86400, {"from": accounts[2]}
            ).return_value
        )

        wedding_contract.revokeEngagement({"from": accounts[2]})

        for acc in accounts[2:6]:
            with brownie.reverts("The wedding has been canceled"):
                wedding_contract.getMyPartnersAddresses({"from": acc})

    def test_correct_list_of_partners_returned(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[2:6], chain.time() + 86400, []
        )

        for acc in accounts[2:6]:
            assert (
                wedding_contract.getMyPartnersAddresses({"from": acc}) == accounts[2:6]
            )
