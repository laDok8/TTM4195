// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

contract MyContract {
    uint256 internal value;

    function getValue() public view returns (uint256) {
        return value;
    }

    function getValueWithoutViewModifier() public returns (uint256) {
        return value;
    }

    function setValue(uint256 _value) public {
        value = _value;
    }
}
