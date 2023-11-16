// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/proxy/Proxy.sol";
import "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract MyImplementation {
    uint256 public value;

    function setValue(uint256 _value) public {
        value = _value;
    }

    function getValue() public view returns (uint256) {
        return value;
    }

    function executeLoop(uint256 _times) public {
        for (uint256 i = 0; i < _times; i++) {
            value++;
        }
    }
}

contract MyProxy is ERC1967Proxy {
    constructor(address _logic) ERC1967Proxy(_logic, "") {}
}
