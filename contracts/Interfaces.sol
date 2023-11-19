// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";

interface IWeddingContract {
    function initialize(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external;

    function approveGuest(address _guest) external;

    function revokeEngagement() external;

    function voteAgainstWedding() external;

    function confirmWedding() external;

    function divorce() external;
}

// this interface does NOT list all the functions of the contract, only the ones that are needed for enabling a basic functionality
interface IWeddingRegistry is IERC721Enumerable {
    function isAuthority(address _address) external view returns (bool);

    function initiateWedding(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external returns (address);

    function issueWeddingCertificate(address[] memory _fiances) external;

    function burnWeddingCertificate() external;
}
