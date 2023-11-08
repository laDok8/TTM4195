// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "./Interfaces.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract WeddingRegistry is IWeddingRegistry, ERC721 {
    address[] public authorities;

    mapping(address => address) internal fianceAddressToWeddingContract; // for checking whether a address is married
    mapping(address => address[]) internal weddingContractToFiances;

    uint256 public weddingContractCount = 0;

    function isAuthority(address _address) public view returns (bool) {
        for (uint32 i = 0; i < authorities.length; i++) {
            if (authorities[i] == _address) {
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

    function updateAuthorities(
        address[] memory _authorities
    ) external onlyAuthorities {
        // TODO check that authorities are not empty
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
        return weddingContractToFiances[_address].length > 0;
    }

    function isMarried(address _address) internal view returns (bool) {
        /* Checks whether a address is married by checking whether there is a wedding 
        contract address associated with the address and if so whether the wedding was 
        successful.
        */
        if (fianceAddressToWeddingContract[_address] == address(0)) {
            return false;
        } else {
            return
                IWeddingContract(fianceAddressToWeddingContract[_address])
                    .getWeddingSuccessful();
        }
    }

    constructor(address[] memory _authorities) {
        authorities = _authorities;
    }

    function initiateWedding(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external returns (address) {
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
        address newContractAddr = address(
            new WeddingContract(_fiances, _weddingDate, weddingContractCount++)
        );
        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[_fiances[i]] = newContractAddr;
        }
        weddingContractToFiances[newContractAddr] = _fiances;

        return newContractAddr;
    }

    function getMyWeddingContractAddress() external view returns (address) {
        require(isMarried(msg.sender), "The fiance is not married"); // there can still be a contract address at someones address if the wedding was canceled
        return fianceAddressToWeddingContract[msg.sender];
    }
}
