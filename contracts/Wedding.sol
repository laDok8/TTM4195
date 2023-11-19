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

    uint32 public constant durationOfWedding = 86400; // 24 hours in seconds, time interval of the duration of the wedding

    uint16 public constant timeToVote = 36000; // 10 hours in seconds, time interval at the wedding day in which the guests can vote against the wedding

    event inviteSent(address invitee);
    event weddingConfirmed(address confirmedFiance);
    event weddingCanceled(address canceler);
    event divorceInitiated(address initiator);
    event voteAgainstWeddingOccured(address voter);

    //// modifiers
    modifier onlyBeforeWeddingDay() {
        /* The wedding day is considered as the day on which the wedding takes place.
        The provided timestamp can be any timestamp on the wedding day.
        For a timestamp to be before the wedding day, it must be smaller than the start of the wedding day.
        Functions with this modifier can only be called before the wedding day.
        */
        uint32 startOfDay = weddingDate - (weddingDate % durationOfWedding); // Convert to start of the day
        require(
            block.timestamp < startOfDay,
            "Action can only be performed before the wedding day"
        );
        _;
    }

    modifier onlyOnWeddingDayAfterVoting() {
        /* There is a predefined time interval on the wedding day in which the guests can vote against the wedding.
        After this time interval, the fiances can confirm the wedding.
        Functions with this modifier can only be called on the wedding day after the voting period ended.
        */
        uint32 startOfDay = weddingDate - (weddingDate % durationOfWedding); // Convert to start of the day
        require(
            block.timestamp >= startOfDay + timeToVote &&
                block.timestamp < startOfDay + durationOfWedding,
            "Action can only be performed during the wedding day after the voting happened"
        );
        _;
    }

    modifier onlyAfterWeddingDay() {
        /* The wedding day is considered as the day on which the wedding takes place.
        The provided timestamp can be any timestamp on the wedding day.
        For a timestamp to be after the wedding day, it must be greater than the end of the wedding day.
        Functions with this modifier can only be called after the wedding day.
        */
        uint32 startOfDay = weddingDate - (weddingDate % durationOfWedding); // Convert to start of the day
        require(
            block.timestamp >= startOfDay + durationOfWedding,
            "Action can only be performed after the wedding day"
        );
        _;
    }

    modifier onlyOnWeddingDayBeforeVotingEnd() {
        /* There is a predefined time interval on the wedding day in which the guests can vote against the wedding.
        After this time interval, the fiances can confirm the wedding.
        Functions with this modifier can only be called on the wedding day before the voting period ends.
        */
        uint32 startOfDay = weddingDate - (weddingDate % durationOfWedding); // Convert to start of the day
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

    modifier onlyGuestsWithVotingRight() {
        /* Only guests which are approved by all fiances and did not vote against the 
        wedding already can call functions with this modifier. */
        require(
            approvedGuests[msg.sender] && !votedAgainstWedding[msg.sender],
            "Only guests with voting right can call this function"
        );
        _;
    }

    modifier onlyNotCanceled() {
        /* A wedding can be canceled by one of the fiances before the wedding day.
        A wedding can be canceled by the guests if more than half of the guests vote against the wedding.
        A wedding is also considered as canceled if the wedding got divorced.
        Functions with this modifier can only be called if the wedding is not canceled.
        */
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
        /* Checks if an array contains duplicates. 
        This uses a basic O(n^2) algorithm. Therfore we require that the array is not too long.
        Since this function is only used once to check the fiances in the constructor and
        it can be assumed that the number of fiances is small, this is not a problem.
        */
        require(array.length < 256, "Array too long");
        for (uint8 i = 0; i < array.length; i++) {
            for (uint8 j = 0; j < i; j++) {
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
        /* Initializes the contract with the provided fiances and wedding date.
        Replaces the constructor because of the proxy pattern.
        The initializer modifier ensures that this function can only be called once.
        */
        require(!hasDuplicates(_fiances), "Duplicate fiance addresses");

        require(_fiances.length > 1, "At least two fiances are required");

        require(
            _weddingDate - (_weddingDate % durationOfWedding) > block.timestamp,
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
        If a guest is already approved by the caller, nothing happens.
        Can only be called by fiances and only before the wedding day and only if the wedding is not canceled.
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
        /* Allows the fiances to revoke the engagement before the wedding day.
        Can only be called by fiances and only before the wedding day and only if the wedding is not canceled.
        Emits an event and cancels the wedding.
        */
        isCanceled = true;

        emit weddingCanceled(msg.sender);
    }

    function voteAgainstWedding()
        external
        onlyOnWeddingDayBeforeVotingEnd
        onlyGuestsWithVotingRight
        onlyNotCanceled
    {
        /* Votes against the wedding. If more than half of the guests vote against the wedding, the wedding is canceled.
        Can only be called by approved guests and only on the wedding day before the voting period ends.
        Can onyl be called once per guest.
        */

        // add the sender to the list of guests who voted against the wedding
        votedAgainstWedding[msg.sender] = true;
        votedAgainstWeddingCounter++;
        emit voteAgainstWeddingOccured(msg.sender);

        // cancel the wedding if more than half of the guests voted against it
        if (votedAgainstWeddingCounter * 2 > approvedGuestsCounter) {
            isCanceled = true;
            emit weddingCanceled(msg.sender);
        }
    }

    function confirmWedding()
        external
        onlyFiances
        onlyOnWeddingDayAfterVoting
        onlyNotCanceled
    {
        /* Confirms the wedding. If all fiances confirm the wedding the registry is called 
        to issue a wedding certificate.
        Can only be called by fiances and only on the wedding day after the voting period ended.
        If the confirmation is not done by all fiances, this contract remains but no token 
        gets minted so the fiances are not considered as married.
        */
        // Mark the confirmation for the sender
        fiancesConfirmations[msg.sender] = true;
        emit weddingConfirmed(msg.sender);

        // Check if all fiances have confirmed
        bool allConfirmed = true;
        for (uint32 i = 0; i < fiances.length; i++) {
            if (!fiancesConfirmations[fiances[i]]) {
                allConfirmed = false;
                break;
            }
        }

        // If all fiances have confirmed, issue a wedding certificate from the registry
        if (allConfirmed) {
            wedReg.issueWeddingCertificate(fiances);
        }
    }

    function divorce() external onlyAfterWeddingDay onlyNotCanceled {
        /* Attempt to burn the marriage. Can only be called by fiances or authorities.
        Can only be called after the wedding day and only if the wedding is not canceled.
        To burn either 2 fiances or 1 fiance and 1 authority must call this function.
        The registry is called to burn the wedding certificate and mark the fiances as divorced.
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
            emit divorceInitiated(msg.sender);
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

    function getMyPartnersAddresses()
        external
        view
        onlyFiances
        onlyNotCanceled
        returns (address[] memory)
    {
        /* Returns the addresses of the partners of the caller. 
        Can only be called by fiances.
        Even if the fiances are not married yet, this function returns the addresses of the partners.
        Only a convenience function for the end user.
        */
        return fiances;
    }
}
