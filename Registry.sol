// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

// NFT related import(s)
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721.sol";

contract WeddingRegistry is ERC721 {
    address[] authorities;
    mapping(address => uint256) public add2cert; // {address : tokenId} stores the wedding certificate of the address
    mapping(uint256 => address[]) public cert2add; // {tokenId : [address1, address2]} stores the addresses of the fiances

    modifier onlyAuthorities() {
        require(
            isAuthority(msg.sender),
            "Only authorized accounts can call this function"
        );
        _;
    }

    function isAuthority(address _address) internal view returns (bool) {
        for (uint32 i = 0; i < authorities.length; i++) {
            if (authorities[i] == _address) {
                return true;
            }
        }
        return false;
    }

    constructor(address[] _authorities) ERC721("Wedding", "WED") {
        authorities = _authorities;
    }

    function updateAuthorities(address[] _authorities) public onlyAuthorities {
        authorities = _authorities;
    }

    function isMarried(address _address) public view returns (bool) {
        return add2cert[_address] != 0;
    }

    function issueWeddingCertificate(address[] fiances_addresses) public {
        require(!isMarried(_address), "Address is already married");
        // owner of the certificate is the registry itself, use the total supply as the token id, and the token uri as the wedding certificate
        uint256 tokenId = totalSupply() + 1;
        _safeMint(address(this), tokenId);

        for (uint32 i = 0; i < fiances_addresses.length; i++) {
            add2cert[fiances_addresses[i]] = tokenId;
        }
        cert2add[tokenId] = fiances_addresses;
    }

    function cancelMarriage() public {
        require(isMarried(msg.sender), "Address is not married");
        uint256 tokenId = add2cert[msg.sender];
        _burn(tokenId);
        delete add2cert[msg.sender];
        delete cert2add[tokenId];
    }
}

// constructor(name_, symbol_)
// supportsInterface(interfaceId)
// balanceOf(owner)
// ownerOf(tokenId)
// name()
// symbol()
// tokenURI(tokenId)
// _baseURI()
// approve(to, tokenId)
// getApproved(tokenId)
// setApprovalForAll(operator, approved)
// isApprovedForAll(owner, operator)
// transferFrom(from, to, tokenId)
// safeTransferFrom(from, to, tokenId)
// safeTransferFrom(from, to, tokenId, data)
// _ownerOf(tokenId)
// _getApproved(tokenId)
// _isAuthorized(owner, spender, tokenId)
// _checkAuthorized(owner, spender, tokenId)
// _increaseBalance(account, value)
// _update(to, tokenId, auth)
// _mint(to, tokenId)
// _safeMint(to, tokenId)
// _safeMint(to, tokenId, data)
// _burn(tokenId)
// _transfer(from, to, tokenId)
// _safeTransfer(from, to, tokenId)
// _safeTransfer(from, to, tokenId, data)
// _approve(to, tokenId, auth)
// _approve(to, tokenId, auth, emitEvent)
// _setApprovalForAll(owner, operator, approved)
// _requireOwned(tokenId)
