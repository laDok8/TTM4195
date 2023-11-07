// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

// NFT related import(s)
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract WeddingContract is ERC721URIStorage {
    uint32 public weddingDate; // Considered as unix time, can be any timestamp but for the calculation the start of the day will be inferred, set in constructor
    address[] public fiances; // Store the fiances' addresses, set in constructor
    address[] public authorities; // Store the authorities' addresses, set in constructor

    mapping(address => mapping(address => bool)) public potentialGuests; // {guest_address : {fiance_address : true/false}} stores all proposed guests and their approvals by the fiances
    address public approvedGuests; // Store the approved guests' addresses
    address[] public votedAgainstWedding; // Store the addresses of the guests who voted against the wedding

    bool[] public fiancesConfirmations; // stores the confirmations of the fiances for the wedding

    address internal fianceWhichWantsToBurn;
    bool internal authorityApprovedBurning = false;
    address internal contractCreator; // Store the creator's address in case of destruction

    uint16 public timeToVote = 36000; // 10 hours in seconds

    event inviteSent(address invitee);

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
        address[] memory _fiances,
        address[] memory _authorities,
        uint32 _weddingDate
    ) ERC721("Wedding", "WED") {
        fiances = _fiances;
        authorities = _authorities;
        weddingDate = _weddingDate;
        contractCreator = msg.sender;

        // initially set all fiances confirmations to false
        for (uint32 i = 0; i < _fiances.length; i++) {
            fiancesConfirmations.push(false);
        }
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
        guestApprovals[_guest][msg.sender] = true;

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
        selfdestruct(payable(contractCreator));
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
            _mint(address(this), 1);
            _setTokenURI(1, "xxx");
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
        if (isAuthority(msg.sender)) {
            authorityApprovedBurning = true;
        }

        // two different spouses want to burn
        if (isFiance(msg.sender) && (fianceWhichWantsToBurn != msg.sender)) {
            _burn(1);
        }

        // a spouse wants to burn and some authority approved
        if (fianceWhichWantsToBurn != address(0) && authorityApprovedBurning) {
            _burn(1);
        }
    }
}
