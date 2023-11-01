// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

// NFT related import(s)
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";


contract WeddingContract is ERC721URIStorage {

    uint32 public weddingDate;  // Considered as unix time
    address[] public fiances;
    address[] public guests;
    address[] public authorities;
    mapping(address => bool) public guestApprovals;
    address internal contractCreator; // Store the creator's address in case of destruction
    bool[] public fiancesConfirmations;
    uint32 public votesAgainstWedding; // Track the number of approved guests who voted against the wedding
    uint32 public approvedGuestsCount; // Track the total number of approved guests
    address internal fianceWhichWantsToBurn;
    bool internal authorityApprovedBurning = false; 

    event inviteSent(address invitee);
    MarriageCertificateNFT public certificateNFT; // Instance of NFT contract


    modifier onlyBeforeWeddingDay() {
        uint32 startOfDay = weddingDay - (weddingDay % 86400); // Convert to start of the day
        require(block.timestamp < startOfDay, "Action can only be performed before the wedding day");
        _;
    }

    modifier onlyOnWeddingDayAfterVoting() {
        uint32 startOfDay = weddingDay - (weddingDay % 86400); // Convert to start of the day
        require(block.timestamp >= startOfDay + 36000 && block.timestamp < startOfDay + 86400, "Action can only be performed during the wedding day after the voting happened");
        _;
    }

    modifier onlyAfterWeddingDay() {
        uint32 startOfDay = weddingDay - (weddingDay % 86400); // Convert to start of the day
        require(block.timestamp >= startOfDay + 86400, "Action can only be performed after the wedding day");
        _;
    }

    modifier onlyDuringFirst10HoursOfWeddingDay() {
        uint32 startOfDay = weddingDay - (weddingDay % 86400); // Convert to start of the day
        require(block.timestamp >= startOfDay && block.timestamp < startOfDay + 36000, "Action can only be performed within the first 10 hours of the wedding day");
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

    modifier onlyGuests() {
        require(isGuest(msg.sender), "Only guests can call this function");
        _;
    }

    function isGuest(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < guests.length; i++) {
            if (guests[i] == _address) {
                return true;
            }
        }
        return false;
    }

    modifier onlyAuthorities() {
        require(isAuthority(msg.sender), "Only authorized accounts can call this function");
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


    constructor(address[] _fiances, address[] _authorities, uint32 _weddingDate) {
        fiances = _fiances;
        authorities = _authorities;
        weddingDate = _weddingDate;
        // Initialize the fiancesConfirmations array
        for (uint32 i = 0; i < _fiances.length; i++) {
            fiancesConfirmations.push(false);
        }
    }


    function proposeGuest(address _guest) external onlyFiances onlyBeforeWeddingDay {
        guests.push(_guest);
        guestApprovals[_guest] = false;
    }

    function approveGuest(address _guest) external onlyFiances onlyBeforeWeddingDay {
        require(isGuest(_guest), "Address is not in the guest list");
        require(!guestApprovals[_guest]["approved"], "Guest is already confirmed");
        // Mark the approval
        guestApprovals[_guest][msg.sender] = true;

        // Check if all fiances have approved the guest
        bool allApproved = true;
        for (uint32 i = 0; i < fiances.length; i++) {
            if (!guestApprovals[_guest][fiances[i]]) {
                allApproved = false;
                break;
            }
        }

        // If all fiances have approved, emit an event and consider the guest approved
        if (allApproved) {
            guestApprovals[_guest]["approved"] = true;
            approvedGuestsCount++;
            emit inviteSent(guest);
        }

    }


    function revokeEngagement() external onlyFiances onlyBeforeWeddingDay {
        selfdestruct(payable(contractCreator));
    }


    function voteAgainstWedding() external onlyGuests onlyDuringFirst10HoursOfWeddingDay {
        require(guestApprovals[_guest]["approved"], "Sender is not an approved guest");

        votesAgainstWedding++;
        guestApprovals[_guest]["approved"] = false;  // to make sure no one votes twice

        if (voteAgainstWedding >= approvedGuestsCount / 2) {
            selfdestruct(payable(contractCreator));
        }
    }


    function confirmWedding() external onlyFiances onlyOnWeddingDayAfterVoting {
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
        
        if (allConfirmed) {
            _mint(address(this), 1);
            _setTokenURI(1, "xxx");
        }
    }


    // one of the spouses + authority can burn the marriage
    function burnMarriage() external onlyFiances onlyAuthorities onlyAfterWeddingDay {
        if (isFiance(msg.sender) && (fianceWhichWantsToBurn == null)) {
            fianceWhichWantsToBurn = msg.sender;
        }

        if (isAuthority(msg.sender)) {
            authorityApprovedBurning = true;
        }

        // two different spouses want to burn
        if (isFiance(msg.sender) && (fianceWhichWantsToBurn != msg.sender)) {
            _burn(address(this), 1);
        }

        // a spouse wants to burn and some authority approved
        if(fianceWhichWantsToBurn != null && authorityApprovedBurning) {
            _burn(address(this), 1);
        }
    }
}