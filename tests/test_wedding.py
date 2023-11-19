import pytest
import brownie

from brownie import WeddingRegistry, WeddingContract


from fixtures import (
    create_registry_contract,
    add_succesfull_wedding,
    add_pending_wedding,
    divorce_wedding,
    add_pending_wedding_non_approved_guests,
)

DAY_IN_SECONDS = 86400
START_TO_VOTE_SECONDS = 36000

class TestRevokeEngagement:
    def test_no_functions_callable_after_revoke(self, chain, accounts):
        # Test setup
        authorities = accounts[0:2]
        fiances = accounts[2:5]
        guests = accounts[5:9]
        unknowns = accounts[9:]
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS

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
        wedding_date = chain.time() + DAY_IN_SECONDS
        start_of_wedding_day = wedding_date - (wedding_date % DAY_IN_SECONDS);

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
        wedding_date = chain.time() + DAY_IN_SECONDS
        start_of_wedding_day = wedding_date - (wedding_date % DAY_IN_SECONDS);

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
        wedding_date = chain.time() + DAY_IN_SECONDS
        start_of_wedding_day = wedding_date - (wedding_date % DAY_IN_SECONDS);

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
        wedding_date = chain.time() + DAY_IN_SECONDS
        start_of_wedding_day = wedding_date - (wedding_date % DAY_IN_SECONDS);

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

    @pytest.mark.skip
    def create_generic_wedding_no_guests(self, chain, accounts, num_guests=6):
        registry_contract = create_registry_contract(accounts[0:2])
        fiances = accounts[2:4]
        guests = accounts[4:4+num_guests]

        start_of_day = (chain.time() // DAY_IN_SECONDS) * DAY_IN_SECONDS
        wedding_date = start_of_day + 3 *DAY_IN_SECONDS # start of 3rd day
        wedding_contract = add_pending_wedding_non_approved_guests(chain, registry_contract, fiances, wedding_date, guests)

        before_wedding_date = wedding_date - DAY_IN_SECONDS
        chain.mine(timestamp=before_wedding_date)
        return fiances, guests, wedding_contract, wedding_date

    @pytest.mark.skip
    def create_generic_wedding(self, chain, accounts, num_guests=6):
        fiances, guests, wedding_contract, wedding_date = self.create_generic_wedding_no_guests(chain, accounts, num_guests)
        for g in guests:
            wedding_contract.approveGuest(g, {"from": fiances[0]})
            wedding_contract.approveGuest(g, {"from": fiances[1]})
        return fiances, guests, wedding_contract, wedding_date



    #this nondeterministic test fails sometimes
    def test_only_callable_on_wedding_day_before_deadline(self, chain, accounts):
        _, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts)

        with brownie.reverts("Action can only be performed within the first 10 hours of the wedding day"):
            wedding_contract.voteAgainstWedding({"from": guests[0]})
        chain.mine(timestamp=wedding_date-1)
        with brownie.reverts("Action can only be performed within the first 10 hours of the wedding day"):
            wedding_contract.voteAgainstWedding({"from": guests[0]})
        chain.mine(timestamp=wedding_date)
        wedding_contract.voteAgainstWedding({"from": guests[1]})
        chain.mine(timestamp=wedding_date+START_TO_VOTE_SECONDS-1)
        wedding_contract.voteAgainstWedding({"from": guests[2]})
        chain.mine(timestamp=wedding_date + START_TO_VOTE_SECONDS)
        with brownie.reverts("Action can only be performed within the first 10 hours of the wedding day"):
            wedding_contract.voteAgainstWedding({"from": guests[0]})

    def test_only_callable_by_guest(self, chain, accounts):
        _, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts)

        chain.mine(timestamp=wedding_date)
        non_approved_guest = [guest for guest in accounts[:12] if guest not in guests]

        for no_guest in non_approved_guest:
            with brownie.reverts("Only guests with voting right can call this function"):
                wedding_contract.voteAgainstWedding({"from": no_guest})

    def test_only_callable_by_approved_guest(self, chain, accounts):
        fiances, guests, wedding_contract, wedding_date = self.create_generic_wedding_no_guests(chain, accounts)

        # approve guests by 1st fiance
        for g in guests:
            wedding_contract.approveGuest(g, {"from": fiances[0]})

        chain.mine(timestamp=wedding_date)

        for g in guests:
            with brownie.reverts("Only guests with voting right can call this function"):
                wedding_contract.voteAgainstWedding({"from": g})

        chain.mine(timestamp=wedding_date - 2)

        # approve guests by 2nd fiance
        for g in guests:
            wedding_contract.approveGuest(g, {"from": fiances[1]})

        chain.mine(timestamp=wedding_date)
        wedding_contract.voteAgainstWedding({"from": guests[0]})

    def test_only_callable_once_per_guest(self, chain, accounts):
        fiances, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date)

        # vote
        for g in guests[:len(guests)//2 -1]:
            print(len(fiances))
            wedding_contract.voteAgainstWedding({"from": g})
            with brownie.reverts("Only guests with voting right can call this function"):
                wedding_contract.voteAgainstWedding({"from": g})

    def test_only_callable_if_not_cancelled(self, chain, accounts):
        fiances, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts)

        # cancel
        wedding_contract.revokeEngagement({"from": fiances[0]})
        with brownie.reverts("Action can only be performed within the first 10 hours of the wedding day"):
            wedding_contract.voteAgainstWedding({"from": guests[0]})
        chain.mine(timestamp=wedding_date)
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.voteAgainstWedding({"from": guests[0]})

    def test_no_approved_guests(self, chain, accounts):
        _, guests, wedding_contract, wedding_date = self.create_generic_wedding_no_guests(chain, accounts)
        chain.mine(timestamp=wedding_date)
        for g in guests:
            with brownie.reverts("Only guests with voting right can call this function"):
                wedding_contract.voteAgainstWedding({"from": g})

    def test_event_sent_after_vote(self, chain, accounts):
        fiances, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date)
        tx = wedding_contract.voteAgainstWedding({"from": guests[0]})
        assert len(tx.events) == 1

    def test_event_sent_after_majority_vote(self, chain, accounts):
        _, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date)
        for g in guests[:len(guests)//2]:
            wedding_contract.voteAgainstWedding({"from": g})
        tx = wedding_contract.voteAgainstWedding({"from": guests[len(guests)//2]})
        assert len(tx.events) == 2

    @pytest.mark.parametrize("m, n", [(0, 0), (0, 1), (1, 3), (2, 3), (3, 3)])
    def test_n_out_of_m_guests_voted_against(self, chain, accounts , m, n):
        _, guests, wedding_contract, wedding_date = self.create_generic_wedding(chain, accounts, num_guests= n)
        chain.mine(timestamp=wedding_date)
        for idx, g in enumerate(guests[:m]):
            if idx * 2 > m:
                with brownie.reverts("The wedding has been canceled"):
                    wedding_contract.voteAgainstWedding({"from": g})
            else:
                wedding_contract.voteAgainstWedding({"from": g})


class TestConfirmWedding:

    @pytest.mark.skip
    def create_generic_wedding(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        fiances = accounts[2:4]

        start_of_day = (chain.time() // DAY_IN_SECONDS) * DAY_IN_SECONDS
        wedding_date = start_of_day + 3 *DAY_IN_SECONDS # start of 3rd day
        wedding_contract = add_pending_wedding_non_approved_guests(chain, registry_contract, fiances, wedding_date, [])

        before_wedding_date = wedding_date - DAY_IN_SECONDS
        chain.mine(timestamp=before_wedding_date)
        return fiances, wedding_contract, wedding_date, registry_contract

    def test_only_callable_by_fiances(self, chain, accounts):
        fiances, wedding_contract, wedding_date, _ = self.create_generic_wedding(chain, accounts)
        non_fiance = [acc for acc in accounts[:12] if acc not in fiances]
        chain.mine(timestamp=wedding_date)
        for acc in non_fiance:
            with brownie.reverts("Only fiances can call this function"):
                wedding_contract.confirmWedding({"from": acc})

    def test_only_callable_on_wedding_day_after_voting_deadline(self, chain, accounts):
        fiances, wedding_contract, wedding_date, _ = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date)
        with brownie.reverts("Action can only be performed during the wedding day after the voting happened"):
            wedding_contract.confirmWedding({"from": fiances[0]})
        chain.mine(timestamp=wedding_date  + START_TO_VOTE_SECONDS)
        wedding_contract.confirmWedding({"from": fiances[0]})

    def test_only_callable_if_not_cancelled(self, chain, accounts):
        fiances, wedding_contract, wedding_date, _ = self.create_generic_wedding(chain, accounts)
        wedding_contract.revokeEngagement({"from": fiances[0]})
        chain.mine(timestamp=wedding_date+START_TO_VOTE_SECONDS)
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.confirmWedding({"from": fiances[0]})

    def test_double_confirm_does_not_change_anything(self, chain, accounts):
        fiances, wedding_contract, wedding_date, _ = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date+START_TO_VOTE_SECONDS)
        wedding_contract.confirmWedding({"from": fiances[0]})
        wedding_contract.confirmWedding({"from": fiances[0]})

    def test_wedding_certificate_issued_after_final_confirm(self, chain, accounts):
        fiances, wedding_contract, wedding_date, registry_contract = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date+START_TO_VOTE_SECONDS)
        wedding_contract.confirmWedding({"from": fiances[0]})
        wedding_contract.confirmWedding({"from": fiances[1]})
        assert registry_contract.getMyWeddingTokenId({"from": fiances[0]}) == 0

    def test_no_certificate_issued_if_not_all_fiances_confirmed(self, chain, accounts):
        fiances, wedding_contract, wedding_date, registry_contract = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date+START_TO_VOTE_SECONDS)
        wedding_contract.confirmWedding({"from": fiances[0]})
        with brownie.reverts("Only married accounts can call this function"):
            registry_contract.getMyWeddingTokenId({"from": fiances[0]})
        with brownie.reverts("Only married accounts can call this function"):
            registry_contract.getMyWeddingTokenId({"from": fiances[1]})

    def test_event_emitted_after_each_confirm(self, chain, accounts):
        fiances, wedding_contract, wedding_date, _ = self.create_generic_wedding(chain, accounts)
        chain.mine(timestamp=wedding_date+START_TO_VOTE_SECONDS)
        tx = wedding_contract.confirmWedding({"from": fiances[0]})
        assert len(tx.events) == 1
        tx = wedding_contract.confirmWedding({"from": fiances[1]})
        assert len(tx.events) == 3

class TestDivorce:
    @pytest.mark.skip
    def create_finished_wedding(self, chain, accounts):
        authorities = accounts[0:2]
        registry_contract = create_registry_contract(authorities)
        fiances = accounts[2:4]

        start_of_day = (chain.time() // DAY_IN_SECONDS) * DAY_IN_SECONDS
        wedding_date = start_of_day + 3 *DAY_IN_SECONDS # start of 3rd day
        wedding_time = wedding_date + START_TO_VOTE_SECONDS
        wedding_contract = add_pending_wedding(chain, registry_contract, fiances, wedding_date, [])
        chain.mine(timestamp=wedding_time)

        # confirm wedding
        wedding_contract.confirmWedding({"from": fiances[0]})
        wedding_contract.confirmWedding({"from": fiances[1]})

        return authorities, fiances, wedding_contract, wedding_time, registry_contract

    def test_only_callable_after_wedding_day(self, chain, accounts):
        _, fiances, wedding_contract, _ , _= self.create_finished_wedding(chain, accounts)
        with brownie.reverts("Action can only be performed after the wedding day"):
            wedding_contract.divorce({"from": fiances[0]})

    def test_only_callable_if_not_cancelled(self, chain, accounts):
        _, fiances, wedding_contract, wedding_time, _ = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": fiances[0]})
        wedding_contract.divorce({"from": fiances[1]})
        with brownie.reverts("The wedding has been canceled"):
            wedding_contract.divorce({"from": fiances[0]})

    def test_only_callable_by_fiances_or_authorities(self, chain, accounts):
        authorities, fiances, wedding_contract, wedding_time, _ = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        non_authorized = [acc for acc in accounts[:12] if acc not in [*fiances, *authorities]]
        for acc in non_authorized:
            with brownie.reverts("Only fiances or authorities can call this function"):
                wedding_contract.divorce({"from": acc})

    def test_divorce_by_2_spouses(self, chain, accounts):
        _, fiances, wedding_contract, wedding_time, registry_contract = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": fiances[0]})
        wedding_contract.divorce({"from": fiances[1]})
        with brownie.reverts("Only married accounts can call this function"):
            registry_contract.getMyWeddingTokenId({"from": fiances[0]})

    def test_divorce_by_1_spouse_and_1_authority(self, chain, accounts):
        authorities, fiances, wedding_contract, wedding_time, registry_contract = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": fiances[0]})
        wedding_contract.divorce({"from": authorities[0]})
        with brownie.reverts("Only married accounts can call this function"):
            registry_contract.getMyWeddingTokenId({"from": fiances[0]})

    def test_divorce_fails_if_2_authorities(self, chain, accounts):
        authorities, fiances, wedding_contract, wedding_time, registry_contract = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": authorities[0]})
        with brownie.reverts("Authority already initiated divorce"):
                wedding_contract.divorce({"from": authorities[1]})
        assert registry_contract.getMyWeddingTokenId({"from": fiances[0]}) == 0

    def test_divorce_can_only_be_called_once_per_fiance(self, chain, accounts):
        _, fiances, wedding_contract, wedding_time, registry_contract = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": fiances[0]})
        with brownie.reverts("You already initiated or approved divorce"):
            wedding_contract.divorce({"from": fiances[0]})

    def test_initiate_wedding_possible_after_divorce(self, chain, accounts):
        _, fiances, wedding_contract, wedding_time, registry_contract = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": fiances[0]})
        wedding_contract.divorce({"from": fiances[1]})
        registry_contract.initiateWedding(
            fiances, wedding_time+10*DAY_IN_SECONDS, {"from": fiances[0]}
        )

    def test_event_emitted_after_divorce_initiated(self, chain, accounts):
        _, fiances, wedding_contract, wedding_time, _ = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        tx = wedding_contract.divorce({"from": fiances[0]})
        assert len(tx.events) == 1

    def test_event_emitted_after_successful_divorce(self, chain, accounts):
        _, fiances, wedding_contract, wedding_time, _ = self.create_finished_wedding(chain, accounts)
        chain.mine(timestamp=wedding_time+DAY_IN_SECONDS)
        wedding_contract.divorce({"from": fiances[0]})
        tx = wedding_contract.divorce({"from": fiances[1]})
        assert len(tx.events) == 2

class TestGetMyPartners:
    def test_getMyPartners_only_callable_by_fiances(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[2:6], chain.time() + DAY_IN_SECONDS, []
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
            chain, registry_contract, accounts[2:6], chain.time() + DAY_IN_SECONDS, []
        )

        chain.mine(timestamp=chain.time() + DAY_IN_SECONDS)
        divorce_wedding(wedding_contract, accounts[2:4])

        for acc in accounts[2:4]:
            with brownie.reverts("The wedding has been canceled"):
                wedding_contract.getMyPartnersAddresses({"from": acc})

    def test_getMyPartners_not_callable_after_revoke(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = WeddingContract.at(
            registry_contract.initiateWedding(
                accounts[2:6], chain.time() + DAY_IN_SECONDS, {"from": accounts[2]}
            ).return_value
        )

        wedding_contract.revokeEngagement({"from": accounts[2]})

        for acc in accounts[2:6]:
            with brownie.reverts("The wedding has been canceled"):
                wedding_contract.getMyPartnersAddresses({"from": acc})

    def test_correct_list_of_partners_returned(self, chain, accounts):
        registry_contract = create_registry_contract(accounts[0:2])
        wedding_contract = add_succesfull_wedding(
            chain, registry_contract, accounts[2:6], chain.time() + DAY_IN_SECONDS, []
        )

        for acc in accounts[2:6]:
            assert (
                wedding_contract.getMyPartnersAddresses({"from": acc}) == accounts[2:6]
            )
