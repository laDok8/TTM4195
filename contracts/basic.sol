// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/proxy/Proxy.sol";

contract MyImplementation {
    uint256 public value;

    function setValue(uint256 _value) public {
        value = _value;
    }

    function getValue() public view returns (uint256) {
        return value;
    }
}

interface IMyImplementation {
    function setValue(uint256 _value) external;

    function getValue() external view returns (uint256);
}

contract MyProxy is Proxy, MyImplementation {
    address internal logic;

    constructor(address _logic) {
        logic = _logic;
    }

    function _implementation() internal view override returns (address) {
        return logic;
    }
}
