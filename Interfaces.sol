// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";

interface IWeddingContract {
    function getRegistryAddress() external view returns (address);

    function approveGuest(address _guest) external;

    function revokeEngagement() external;

    function voteAgainstWedding() external;

    function confirmWedding() external;

    function divorce() external;
}

interface IWeddingRegistry is IERC721Enumerable {
    function isAuthority(address _address) external view returns (bool);

    function initiateWedding(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external returns (address);

    function updateAuthorities(address[] memory _authorities) external;

    // function getMyWeddingContractAddress() external view returns (address);

    function issueWeddingCertificate() external returns (uint256);

    function burnWeddingCertificate(uint256 tokenId) external;
}
