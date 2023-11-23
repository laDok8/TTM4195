# from brownie import WeddingRegistry, WeddingContract, accounts, chain


class TestFullWeddingProcedure:
    def test_subset_votest_against_wedding(
        self, wedding_contract, registry_contract, accounts, chain
    ):
        fiances = accounts[3:5]
        guests = accounts[5:9]
        wedding_date = chain.time() + 86400  # wedding is tomorrow

        # approve/invite guests
        for fiance in fiances:
            for guest in guests:
                wedding_contract.approveGuest(guest, {"from": fiance}).wait(1)

        # fast forward to begining of wedding date
        wedding_date_begin = (wedding_date // 86400) * 86400
        chain.mine(timestamp=wedding_date_begin)

        # one guest votes against the wedding
        wedding_contract.voteAgainstWedding({"from": guests[0]}).wait(1)

        # fast forward to ceremony
        ceremony_begin = wedding_date_begin + 36000
        chain.mine(timestamp=ceremony_begin)

        # confirm wedding
        for fiance in fiances:
            wedding_contract.confirmWedding({"from": fiance}).wait(1)

        # show wedding certificate
        for fiance in fiances:
            assert registry_contract.getMyWeddingTokenId({"from": fiance}) == 0
