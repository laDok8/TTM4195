// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "./Interfaces.sol";
import "./Wedding.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

contract WeddingRegistry is IWeddingRegistry, ERC721Enumerable {
    address[] public authorities;

    mapping(address => address) internal fianceAddressToWeddingContract; // for checking whether a address is married
    mapping(address => bool) internal deployedContracts; // for checking whether a calling address belongs to a deployed contract, using a hashmap for O(1) lookup instead of looping through an array

    function _isAuthority(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < authorities.length; i++) {
            if (authorities[i] == _address) {
                return true;
            }
        }
        return false;
    }

    function isAuthority(address _address) external view returns (bool) {
        return _isAuthority(_address);
    }

    modifier onlyAuthorities() {
        require(
            _isAuthority(msg.sender),
            "Only authorized accounts can call this function"
        );
        _;
    }

    function updateAuthorities(
        address[] memory _authorities
    ) external onlyAuthorities {
        // TODO check that authorities are not empty
        authorities = _authorities;
    }

    modifier onlyDeployedContracts() {
        require(
            deployedContracts[msg.sender],
            "Only deployed contracts can call this function"
        );
        _;
    }

    modifier onlyMarried() {
        require(
            isMarried(msg.sender),
            "Only married accounts can call this function"
        );
        _;
    }

    function isMarried(address _address) internal view returns (bool) {
        // ERC21 raises an error if the address is the zero address
        if (fianceAddressToWeddingContract[_address] == address(0)) {
            return false;
        }
        return balanceOf(fianceAddressToWeddingContract[_address]) > 0;
    }

    constructor(address[] memory _authorities) ERC721("Wedding", "WED") {
        authorities = _authorities;
    }

    function noOneMarried(
        address[] memory _fiances
    ) internal view returns (bool) {
        for (uint32 i = 0; i < _fiances.length; i++) {
            if (isMarried(_fiances[i])) {
                return false;
            }
        }
        return true;
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

    function initiateWedding(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external returns (address) {
        // ceck that all fiances are not married by calling the registry
        require(
            noOneMarried(_fiances),
            "One of the fiances is already married"
        );

        require(!hasDuplicates(_fiances), "Duplicate fiance addresses");

        require(_fiances.length > 1, "At least two fiances are required");

        require(
            _weddingDate > (block.timestamp % 86400) + 86400,
            "Wedding date must be at least on the next day"
        );

        // deploy a new wedding contract
        address newContractAddr = address(
            new WeddingContract(_fiances, _weddingDate)
        );
        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[_fiances[i]] = newContractAddr;
        }
        deployedContracts[newContractAddr] = true;

        return newContractAddr;
    }

    function issueWeddingCertificate(
        address[] memory _fiances
    ) external onlyDeployedContracts {
        // TODO assert that none of the fiances has gotten married in the meantime
        require(noOneMarried(_fiances));
        _mint(msg.sender, totalSupply());
    }

    function burnWeddingCertificate() external onlyDeployedContracts {
        _burn(tokenOfOwnerByIndex(msg.sender, 0));
    }

    function getMyWeddingTokenId() external view onlyMarried returns (uint256) {
        return
            tokenOfOwnerByIndex(fianceAddressToWeddingContract[msg.sender], 0);
    }

    function getMyWeddingContractAddress()
        external
        view
        onlyMarried
        returns (address)
    {
        return fianceAddressToWeddingContract[msg.sender];
    }
}
