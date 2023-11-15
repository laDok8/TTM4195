from brownie import WeddingRegistry, accounts, chain, WeddingContract


def main():
    authorities = accounts[0:3]
    fiances = accounts[3:5]
    guests = accounts[5:9]

    registry_contract = WeddingRegistry.deploy(authorities, {"from": authorities[0]})

    wedding_date = chain.time() + 86400
    wedding_contract_addr = registry_contract.initiateWedding(
        fiances, wedding_date, {"from": fiances[0]}
    ).return_value
    wedding_contract = WeddingContract.at(wedding_contract_addr)

    for fiance in fiances:
        for guest in guests:
            wedding_contract.approveGuest(guest, {"from": fiance}).wait(1)

    # fas forward to begining of wedding date
    wedding_date_begin = (wedding_date // 86400) * 86400
    chain.mine(timestamp=wedding_date_begin)

    # one guest votes against the wedding
    wedding_contract.voteAgainstWedding({"from": guests[0]}).wait(1)

    # fast forward to ceremony
    ceremony_begin = wedding_date_begin + 36000
    # chain.sleep(ceremony_begin - chain.time())
    chain.mine(timestamp=ceremony_begin)

    for fiance in fiances:
        wedding_contract.confirmWedding({"from": fiance}).wait(1)

    # show wedding certificate
    for fiance in fiances:
        print(registry_contract.getMyWeddingTokenId({"from": fiance}))
