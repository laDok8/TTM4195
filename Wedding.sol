// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

contract WeddingContract {
    // TODO make variables internal and add getters for fiances
    address public wedReg; // The wedding registry that approves and issues wedding certificates
    uint32 public weddingDate; // Considered as unix time, can be any timestamp but for the calculation the start of the day will be inferred, set in constructor
    address[] public fiances; // Store the fiances' addresses, set in constructor

    mapping(address => mapping(address => bool)) public potentialGuests; // {guest_address : {fiance_address : true/false}} stores all proposed guests and their approvals by the fiances
    address public approvedGuests; // Store the approved guests' addresses
    address[] public votedAgainstWedding; // Store the addresses of the guests who voted against the wedding

    bool[] public fiancesConfirmations; // stores the confirmations of the fiances for the wedding

    address internal fianceWhichWantsToBurn;
    bool internal authorityApprovedBurning = false;

    bool internal weddingSuccessful = false;
    uint256 internal weddingId;

    uint16 public timeToVote = 36000; // 10 hours in seconds

    event inviteSent(address invitee);
    // TODO more events

    modifier onlyBeforeWeddingDay() {
        uint32 startOfDay = weddingDate - (weddingDate % 86400); // Convert to start of the day
        require(
            block.timestamp < startOfDay,
            "Action can only be performed before the wedding day"
        );
        _;
    }

    modifier onlyOnWeddingDayAfterVoting() {
        uint32 startOfDay = weddingDate - (weddingDate % 86400); // Convert to start of the day
        require(
            block.timestamp >= startOfDay + timeToVote &&
                block.timestamp < startOfDay + 86400,
            "Action can only be performed during the wedding day after the voting happened"
        );
        _;
    }

    modifier onlyAfterWeddingDay() {
        uint32 startOfDay = weddingDate - (weddingDate % 86400); // Convert to start of the day
        require(
            block.timestamp >= startOfDay + 86400,
            "Action can only be performed after the wedding day"
        );
        _;
    }

    modifier onlyOnWeddingDayBeforeVotingEnd() {
        uint32 startOfDay = weddingDate - (weddingDate % 86400); // Convert to start of the day
        require(
            block.timestamp >= startOfDay &&
                block.timestamp < startOfDay + timeToVote,
            "Action can only be performed within the first 10 hours of the wedding day"
        );
        _;
    }

    modifier onlyFiances() {
        require(isFiance(msg.sender), "Only fiances can call this function");
        _;
    }

    function isFiance(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < fiances.length; i++) {
            if (fiances[i] == _address) {
                return true;
            }
        }
        return false;
    }

    modifier onlyApprovedGuests() {
        require(isGuest(msg.sender), "Only guests can call this function");
        _;
    }

    function isApprovedGuest(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < ApprovedGuests.length; i++) {
            if (approvedGuests[i] == _address) {
                return true;
            }
        }
        return false;
    }

    modifier onlyGuestsWithVotingRight() {
        require(
            isApprovedGuest(_address) && !hasVotedAgainstWedding(_address),
            "Only guests with voting right can call this function"
        );
        _;
    }

    function hasVotedAgainstWedding(
        address _address
    ) internal view returns (bool) {
        for (uint32 i = 0; i < votedAgainstWedding.length; i++) {
            if (votedAgainstWedding[i] == _address) {
                return true;
            }
        }
        return false;
    }

    constructor(
        address[] _fiances,
        uint32 _weddingDate,
        uint256 _weddingId
    ) {
        wedReg = msg.sender;

        fiances = _fiances;
        weddingDate = _weddingDate;
        weddingId = _weddingId;

        fiancesConfirmations = new bool[](fiances.length); // by default, all fiances are set to false
    }

    function approveGuest(
        address _guest
    ) external onlyFiances onlyBeforeWeddingDay {
        /* Adds a guest to the address-appovals-mapping of potential guests and marks the approval of the sender.
        If the passed address is already a potential guest, the approval of the sender is marked.
        If the guest is approved by all fiances, the guest is added to the list of approved guests and an event is emitted.
        */

        // preven that a guest is added to the list of approved guests more than once
        require(!isApprovedGuest(_guest), "Guest is already approved");

        // Mark the approval
        potentialGuests[_guest][msg.sender] = true;

        // Check if all fiances have approved the guest
        bool guestApprovedByAllFiances = true;
        for (uint32 i = 0; i < fiances.length; i++) {
            if (!potentialGuests[_guest][fiances[i]]) {
                guestApprovedByAllFiances = false;
                break;
            }
        }

        // If all fiances have approved, emit an event and consider the guest approved
        if (guestApprovedByAllFiances) {
            approvedGuests.push(_guest);
            emit inviteSent(_guest);
        }
    }

    function revokeEngagement() external onlyFiances onlyBeforeWeddingDay {
        /* Destroyes the contract and sends the funds back to the creator.
        This can only be done before the wedding day and only by one of the fiances.
        */
        selfdestruct(payable(wedReg));
    }

    function voteAgainstWedding()
        external
        onlyOnWeddingDayBeforeVotingEnd
        onlyGuestsWithVotingRight
    {
        /* Votes against the wedding. If more than half of the guests vote against the wedding, the contract is destroyed.
        Can only be called by approved guests and only on the wedding day before the voting period ends.
        */

        // add the sender to the list of guests who voted against the wedding
        votedAgainstWedding.push(msg.sender);

        // cancel the wedding if more than half of the guests voted against it
        if (votedAgainstWedding.length >= approvedGuests.length / 2) {
            selfdestruct(payable(contractCreator));
        }
    }

    function confirmWedding() external onlyFiances onlyOnWeddingDayAfterVoting {
        /* Confirms the wedding. If all fiances confirm the wedding, the contract mints a token and sets the tokenURI to "xxx".
        Can only be called by fiances and only on the wedding day after the voting period ended.
        */
        // Mark the confirmation for the sender
        for (uint32 i = 0; i < fiances.length; i++) {
            if (fiances[i] == msg.sender) {
                fiancesConfirmations[i] = true;
                break;
            }
        }

        // Check if all fiances have confirmed
        bool allConfirmed = true;
        for (uint32 i = 0; i < fiancesConfirmations.length; i++) {
            if (!fiancesConfirmations[i]) {
                allConfirmed = false;
                break;
            }
        }

        // issue an NFT if all fiances have confirmed
        if (allConfirmed) {
            // return wedReg.issueWeddingCertificate(address(this)); // fails if one of the fiances has married in the meantime
            weddingSuccessful = true;
        }
    }

    function burnMarriage() external onlyAfterWeddingDay {
        /* Attempt to burn the marriage. If one of the fiances calls this function, the fianceWhichWantsToBurn is set to the sender.
        If an authority calls this function, the authorityApprovedBurning is set to true.
        If two different fiances want to burn, the marriage is burned or one fiance and an authority want to burn, the marriage is burned.
        Can only be called after the wedding day.
        If someone else than a fiance or an authority calls this function, nothing happens.
        (No special modifier was used for this to reduce computational complexity)
        */
        // the "first" fiance to call this function will be set as the fianceWhichWantsToBurn
        if (isFiance(msg.sender) && (fianceWhichWantsToBurn == address(0))) {
            fianceWhichWantsToBurn = msg.sender;
        }

        // an authority can approve the burning, so a single spouse can burn with the authority approval
        if (wedReg.isAuthority(msg.sender)) {
            authorityApprovedBurning = true;
        }

        // two different spouses want to burn
        if (isFiance(msg.sender) && (fianceWhichWantsToBurn != msg.sender)) {
            // wedReg.cancelMarriage(fiances);
            weddingSuccessful = false;
        }

        // a spouse wants to burn and some authority approved
        if (fianceWhichWantsToBurn != address(0) && authorityApprovedBurning) {
            // wedReg.cancelMarriage(fiances);
            weddingSuccessful = false;
        }
    }

    function weddingSuccessful() public view onlyAuthorities returns (bool) {
        return weddingSuccessful;
    }
}


contract WeddingRegistry {
    address[] authorities;
    mapping(address => address) public fianceAddressToWeddingContract; // for checking whether a address is married
    uint256 public weddingContractCount = 0;

    modifier onlyAuthorities() {
        require(
            isAuthority(msg.sender),
            "Only authorized accounts can call this function"
        );
        _;
    }

    function isAuthority(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < authorities.length; i++) {
            if (authorities[i] == _address) {
                return true;
            }
        }
        return false;
    }

    constructor(address[] _authorities) {
        authorities = _authorities;
    }

    function updateAuthorities(address[] _authorities) public onlyAuthorities {
        authorities = _authorities;
    }

    modifier onlyDeployedContracts() {
        require(
            isDeployedContract(msg.sender),
            "Only deployed contracts can call this function"
        );
        _;
    }

    function isDeployedContract(address _address) internal view returns (bool) {
        return weddingContractsToFiances[_address].length > 0;
    }

    function isMarried(address _address) public view returns (bool) {
        /* Checks whether a address is married by checking whether there is a wedding 
        contract address associated with the address and if so whether the wedding was 
        successful.
        */
        weddingContractAddr = fianceAddressToWeddingContract[_address];
        if weddingContractAddr == address(0) {
            return false;
        } else {
            return weddingContractAddr.weddingSuccessful();
        }
    }

    function initiateWedding(
        address[] _fiances,
        uint32 _weddingDate,
    ){
        // ceck that all fiances are not married by calling the registry
        for (uint32 i = 0; i < _fiances.length; i++) {
            require(
                !isMarried(_fiances[i]),
                "One of the fiances is already married"
            );
        }

        // TODO check that the fiances addresses contain no duplicates

        // TODO check that the date is at least the next day

        // deploy a new wedding contract
        address newContractAddr = address(new WeddingContract(_fiances, weddingDate, weddingContractCount++));
        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[_fiances[i]] = newContractAddr;
        }
        // weddingContractToFiances[newContractAddr] = _fiances;

        return newContractAddr;
    }

    function getMyWeddingContractAddress() public view returns (address) {
        require(isMarried(msg.sender), "The fiance is not married"); // there can still be a contract address at someones address if the wedding was canceled
        return fianceAddressToWeddingContract[msg.sender];
    }

    // function issueWeddingCertificate() public onlyDeployedContracts {
    //     // check again that all fiances are not married. In case multiple wedding contracts have been initiated before the wedding date
    //     for (uint32 i = 0; i < weddingContractToFiances[msg.sender].length; i++) {
    //         require(
    //             !isMarried(weddingContractToFiances[msg.sender][i]),
    //             "One of the fiances has married in the meantime"
    //         );
    //     }
        
    //     return tokenId;
    // }

    // function cancelMarriage(address[] fiances) public onlyDeployedContracts {
    //     tokenId = fianceAddressToTokenId[fiances[0]];
    //     _burn(tokenId);
    //     for (uint32 i = 0; i < fiances.length; i++) {
    //         fianceAddressToTokenId[fiances[i]] = 0;
    //     }
    // }
}
