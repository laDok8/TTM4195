// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "./Interfaces.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";

contract WeddingContract is IWeddingContract, Initializable {
    IWeddingRegistry internal wedReg; // The wedding registry that approves and issues wedding certificates
    uint32 internal weddingDate; // Considered as unix time, can be any timestamp but for the calculation the start of the day will be inferred, set in constructor
    address[] internal fiances; // Store the fiances' addresses, set in constructor

    mapping(address => mapping(address => bool)) internal potentialGuests; // {guest_address : {fiance_address : true/false}} stores all proposed guests and their approvals by the fiances
    mapping(address => bool) internal approvedGuests; // Store the approved guests' addresses
    uint16 internal approvedGuestsCounter = 0; // Counter for the approved guest --> we can have max 2**16 guests
    mapping(address => bool) internal votedAgainstWedding; // Store the addresses of the guests who voted against the wedding
    uint16 internal votedAgainstWeddingCounter = 0; // Counter for the guests who voted against the wedding

    mapping(address => bool) internal fiancesConfirmations; // stores the fiances who confirmed the wedding

    address internal divorceInitiator; // stores the address of the fiance who initiated the divorce

    bool internal isCanceled = false; // only needed to revert any function calls if the wedding is canceled (selfdestruct is not used)

    uint16 public constant timeToVote = 36000; // 10 hours in seconds

    event inviteSent(address invitee);
    // TODO more events

    //// modifiers
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

    modifier onlyApprovedGuests() {
        require(
            approvedGuests[msg.sender],
            "Only guests can call this function"
        );
        _;
    }

    modifier onlyGuestsWithVotingRight() {
        require(
            approvedGuests[msg.sender] && !votedAgainstWedding[msg.sender],
            "Only guests with voting right can call this function"
        );
        _;
    }

    modifier onlyNotCanceled() {
        require(!isCanceled, "The wedding has been canceled");
        _;
    }

    //// internal functions
    function isFiance(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < fiances.length; i++) {
            if (fiances[i] == _address) {
                return true;
            }
        }
        return false;
    }

    function hasDuplicates(
        address[] memory array
    ) internal pure returns (bool) {
        for (uint256 i = 0; i < array.length; i++) {
            for (uint256 j = 0; j < i; j++) {
                if (array[i] == array[j]) {
                    return true;
                }
            }
        }

        return false;
    }

    //// constructor
    // not needed anymore because of the proxy pattern --> moved to initialize function

    //// external functions
    function initialize(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external initializer {
        require(!hasDuplicates(_fiances), "Duplicate fiance addresses");

        require(_fiances.length > 1, "At least two fiances are required");

        require(
            _weddingDate - (_weddingDate % 86400) > block.timestamp,
            "Wedding date must be at least on the next day"
        );

        wedReg = IWeddingRegistry(msg.sender);

        fiances = _fiances;
        weddingDate = _weddingDate;
    }

    function approveGuest(
        address _guest
    ) external onlyFiances onlyBeforeWeddingDay onlyNotCanceled {
        /* Adds a guest to the address-appovals-mapping of potential guests and marks the approval of the sender.
        If the passed address is already a potential guest, the approval of the sender is marked.
        If the guest is approved by all fiances, the guest is added to the list of approved guests and an event is emitted.
        */

        // preven that a guest is added to the list of approved guests more than once
        require(!approvedGuests[_guest], "Guest is already approved");

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
            approvedGuests[_guest] = true;
            require(
                type(uint16).max > approvedGuestsCounter,
                "Maximum number of guests reached"
            );
            approvedGuestsCounter++;
            emit inviteSent(_guest);
        }
    }

    function revokeEngagement()
        external
        onlyFiances
        onlyBeforeWeddingDay
        onlyNotCanceled
    {
        /* Destroyes the contract and sends the funds back to the creator.
        This can only be done before the wedding day and only by one of the fiances.
        */
        isCanceled = true;
    }

    function voteAgainstWedding()
        external
        onlyOnWeddingDayBeforeVotingEnd
        onlyGuestsWithVotingRight
        onlyNotCanceled
    {
        /* Votes against the wedding. If more than half of the guests vote against the wedding, the contract is destroyed.
        Can only be called by approved guests and only on the wedding day before the voting period ends.
        */

        // add the sender to the list of guests who voted against the wedding
        votedAgainstWedding[msg.sender] = true;
        votedAgainstWeddingCounter++;

        // cancel the wedding if more than half of the guests voted against it
        if (votedAgainstWeddingCounter > approvedGuestsCounter) {
            isCanceled = true;
        }
    }

    function confirmWedding()
        external
        onlyFiances
        onlyOnWeddingDayAfterVoting
        onlyNotCanceled
    {
        /* Confirms the wedding. If all fiances confirm the wedding, the contract mints a token and sets the tokenURI to "xxx".
        Can only be called by fiances and only on the wedding day after the voting period ended.
        */
        // Mark the confirmation for the sender
        fiancesConfirmations[msg.sender] = true;

        // Check if all fiances have confirmed
        bool allConfirmed = true;
        for (uint32 i = 0; i < fiances.length; i++) {
            if (!fiancesConfirmations[fiances[i]]) {
                allConfirmed = false;
                break;
            }
        }
        // issue an NFT if all fiances have confirmed
        if (allConfirmed) {
            wedReg.issueWeddingCertificate(fiances);
            // TODO emit event
        }
    }

    function divorce() external onlyAfterWeddingDay onlyNotCanceled {
        /* Attempt to burn the marriage. If one of the fiances calls this function, the fianceWhichWantsToBurn is set to the sender.
        If an authority calls this function, the authorityApprovedBurning is set to true.
        If two different fiances want to burn, the marriage is burned or one fiance and an authority want to burn, the marriage is burned.
        Can only be called after the wedding day.
        */
        bool isFiance_ = isFiance(msg.sender);
        bool isAuthority_ = wedReg.isAuthority(msg.sender);

        require(
            isFiance_ || isAuthority_,
            "Only fiances or authorities can call this function"
        );

        require(
            msg.sender != divorceInitiator,
            "You already initiated or approved divorce"
        );

        // if no one has approved/initiated a divorce yet, set the sender as the divorce initiator
        if (divorceInitiator == address(0)) {
            divorceInitiator = msg.sender;
            return;
        }

        // everything from here is onyl executed if there is already a divorce initiator
        // if the sender is an authority make sure that the divorce initiator is a fiance
        if (isAuthority_) {
            require(
                isFiance(divorceInitiator),
                "Authority already initiated divorce"
            );
        }

        // either 2 fiances or 1 fiance and 1 authority want to burn the marriage
        wedReg.burnWeddingCertificate();
        isCanceled = true;
    }
}
