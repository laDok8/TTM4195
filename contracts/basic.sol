// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyImplementation is UUPSUpgradeable, Ownable {
    uint256 public value;

    constructor() Ownable(msg.sender) {}

    function setValue(uint256 _value) public {
        value = _value;
    }

    function getValue() public view returns (uint256) {
        return value;
    }

    function _authorizeUpgrade(address) internal override onlyOwner {}
}

interface IMyImplementation {
    function setValue(uint256 _value) external;

    function getValue() external view returns (uint256);
}

contract MyProxy is ERC1967Proxy {
    constructor(address _implementation) ERC1967Proxy(_implementation, "") {}

    // address internal logic;

    // constructor(address _logic) {
    //     logic = _logic;
    // }

    // function _implementation() internal view override returns (address) {
    //     return logic;
    // }
}
