// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

interface IWeddingContract {
    // function isAuthority(address _address) public view returns (bool);
    function updateAuthorities(address[] memory _authorities) external;

    function initiateWedding(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external returns (address);

    function getMyWeddingContractAddress() external view returns (address);
}

interface IWeddingRegistry is IERC721 {
    function approveGuest(address _guest) external;

    function revokeEngagement(address _fiance) external;

    function voteAgainstWedding() external;

    function confirmWedding() external;

    function divorce() external;
}
