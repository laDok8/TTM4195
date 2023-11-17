// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "./Interfaces.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract WeddingRegistry is IWeddingRegistry, ERC721Enumerable {
    address[] public authorities;
    address internal weddingContractImplementationAddress;

    mapping(address => address) internal fianceAddressToWeddingContract; // for checking whether a address is married
    mapping(address => bool) internal deployedContracts; // for checking whether a calling address belongs to a deployed contract, using a hashmap for O(1) lookup instead of looping through an array

    //// events
    event AuthoritiesUpdated(address[] authorities);
    event WeddingInitiated(
        address weddingContractAddress,
        address[] fiances,
        uint32 weddingDate
    );
    event WeddingCertificateIssued(address[] fiances);
    event WeddingCertificateBurned(address weddingContractAddress);

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
            "Only deployed wedding contracts can call this function"
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

        emit AuthoritiesUpdated(_authorities);
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

        // deploy a new wedding contract proxy (and directly call initialize)
        bytes memory initParams = abi.encodeWithSignature(
            "initialize(address[],uint32)",
            _fiances,
            _weddingDate
        );
        ERC1967Proxy newWeddingProxy_ = new ERC1967Proxy(
            weddingContractImplementationAddress,
            initParams
        );
        IWeddingContract newWeddingProxy = IWeddingContract(
            address(newWeddingProxy_)
        );
        address newWeddingProxyAddress = address(newWeddingProxy);

        // save the address of the new contract in the registry
        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[
                _fiances[i]
            ] = newWeddingProxyAddress;
        }
        deployedContracts[newWeddingProxyAddress] = true;

        emit WeddingInitiated(newWeddingProxyAddress, _fiances, _weddingDate);

        return newWeddingProxyAddress;
    }

    function issueWeddingCertificate(
        address[] memory _fiances
    ) external onlyDeployedContracts {
        require(
            noOneMarried(_fiances),
            "One of the fiances is already married"
        );
        _mint(msg.sender, totalSupply());

        emit WeddingCertificateIssued(_fiances);
    }

    function burnWeddingCertificate() external onlyDeployedContracts {
        _burn(tokenOfOwnerByIndex(msg.sender, 0));

        emit WeddingCertificateBurned(msg.sender);
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
