import pytest
import brownie

from fixtures import (
    create_registry_contract,
    add_succesfull_wedding,
    add_pending_wedding,
    divorce_wedding,
)


class TestRevokeEngagement:
    def test_no_functions_callable_after_revoke(self):
        pass

    def test_revoke_only_callable_before_wedding(self):
        pass

    def test_revoke_only_callable_by_fiances(self):
        pass

    def test_revoke_only_callable_once(self):
        pass


class TestApproveGuests:
    def test_onyl_callable_by_fiances(self):
        pass

    def test_only_callable_before_wedding(self):
        pass

    def test_onyl_callable_when_not_cancelled(self):
        pass

    def test_approved_guest_can_vote(self):
        pass

    def test_guest_not_approved_if_not_all_fiances_approved(self):
        pass

    def test_double_approve_does_not_change_anything(self):
        pass

    def test_guest_can_only_be_approved_once(self):
        pass

    def test_invitation_evet_sent_after_final_approve(self):
        pass


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
