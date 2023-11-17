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
        /* Whether someone is married is determined by whether there is a wedding contract 
        address associated with the address and the balance of the wedding contract address is > 0 */

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
        /* Initialize the authorities and the wedding contract implementation address.
        The wedding contract implementation address is the address of the contract that 
        will implement the logic of a wedding procedure. For each wedding a new proxy contract
        will be deployed that will delegate all calls to the implementation contract.
        The list of authorities must be non-empty.
        */

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
        /* Updates the list of authorities. The list of authorities must be non-empty. 
        Can only be called by an authority. Emit an event when the authorities are updated.
        */
        require(_authorities.length > 0, "Authorities cannot be empty");
        authorities = _authorities;

        emit AuthoritiesUpdated(_authorities);
    }

    function changeWeddingContractImplementationAddress(
        address _weddingContractImplementationAddress
    ) external onlyAuthorities {
        /* Changes the address of the wedding contract implementation.
        This allows for upgrading the wedding contract implementation without having to 
        deploy a new registry. In case the rules for a wedding change, a new implementation
        contract can be deployed and the address can be updated here.
        Can only be called by an authority.
        */
        weddingContractImplementationAddress = _weddingContractImplementationAddress;
    }

    function initiateWedding(
        address[] memory _fiances,
        uint32 _weddingDate
    ) external returns (address) {
        /* Initiates a wedding by deploying a new wedding contract proxy.
        The wedding contract proxy will delegate all calls to the wedding contract implementation
        but maintains its own storage.
        By using a proxy contract, the deployment of a new wedding contract is gas efficient
        as we only need to deploy a new proxy contract and not the whole implementation.
        The wedding contract proxy is initialized with the addresses of the fiances and the wedding date.
        The list of fiances must be non-empty and there must be no duplicate addresses.
        The wedding date must be in the future.
        This requirements are checked by the wedding contract implementation.
        */

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

        // save the address of the new contract in the registry so we can check wether the
        // registry gets called by a wedding contract which was deployed by the registry
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

        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[_fiances[i]] = msg.sender;
        }

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
