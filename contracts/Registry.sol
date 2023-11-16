// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "./Interfaces.sol";
import "./Wedding.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

contract WeddingRegistry is IWeddingRegistry, ERC721Enumerable {
    address[] public authorities;
    address internal weddingContractImplementationAddress;

    mapping(address => address) internal fianceAddressToWeddingContract; // for checking whether a address is married
    mapping(address => bool) internal deployedContracts; // for checking whether a calling address belongs to a deployed contract, using a hashmap for O(1) lookup instead of looping through an array

    // TODO more events

    //// modifiers
    modifier onlyAuthorities() {
        require(
            _isAuthority(msg.sender),
            "Only authorized accounts can call this function"
        );
        _;
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

    //// internal functions
    function _isAuthority(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < authorities.length; i++) {
            if (authorities[i] == _address) {
                return true;
            }
        }
        return false;
    }

    function isMarried(address _address) internal view returns (bool) {
        // ERC21 raises an error if the address is the zero address
        if (fianceAddressToWeddingContract[_address] == address(0)) {
            return false;
        }
        return balanceOf(fianceAddressToWeddingContract[_address]) > 0;
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

    //// constructor
    constructor(
        address[] memory _authorities,
        address _weddingContractImplementationAddress
    ) ERC721("Wedding", "WED") {
        require(_authorities.length > 0, "Authorities cannot be empty");
        authorities = _authorities;

        weddingContractImplementationAddress = _weddingContractImplementationAddress;
    }

    //// external functions
    function isAuthority(address _address) external view returns (bool) {
        return _isAuthority(_address);
    }

    function updateAuthorities(
        address[] memory _authorities
    ) external onlyAuthorities {
        require(_authorities.length > 0, "Authorities cannot be empty");
        authorities = _authorities;
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
            _weddingDate - (_weddingDate % 86400) > block.timestamp,
            "Wedding date must be at least on the next day"
        );

        // deploy a new wedding contract
        WeddingContractProxy newWeddingProxy = new WeddingContractProxy(
            weddingContractImplementationAddress
        );
        newWeddingProxy.initialize(_fiances, _weddingDate);
        address newWeddingProxyAddress = address(newWeddingProxy);
        // save the address of the new contract in the registry
        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[
                _fiances[i]
            ] = newWeddingProxyAddress;
        }
        deployedContracts[newWeddingProxyAddress] = true;

        return newWeddingProxyAddress;
    }

    function issueWeddingCertificate(
        address[] memory _fiances
    ) external onlyDeployedContracts {
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
