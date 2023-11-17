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
    mapping(uint256 => string) internal tokenURIs; // for storing the tokenURI of a wedding token

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
        address associated with the address and the balance of the wedding contract address is > 0.
        A wedding contract address is associated with an address by calling issueWeddingCertificate
        after a successful wedding procedure.
        However, if a wedding contract is canceled, the address of the canceled contract will still be
        associated with the fiances. This is not a problem as the balance of the canceled contract will be 0.
        */

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
    function tokenURI(
        uint256 _tokenId
    ) public view override returns (string memory) {
        /* Returns the token URI of the wedding token with the given token id.
        This URI can be used to retrieve the any kind of metadata of the wedding token.
        */
        return tokenURIs[_tokenId];
    }

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
        /* Issues a wedding certificate to the fiances.
        This function can only be called by a deployed wedding contract. This ensures that
        the ceremony has been executed successfully and was not canceled.
        Issuing a wedding certificate means that the registry will mint a new token and
        associate the token with the wedding contract address.
        The wedding contract address gets associated with the fiances by calling this function.
        The wedding contract address of a married person as well as the wedding token of
        this contract address can be retrieved by calling getMyWeddingContractAddress and
        getMyWeddingTokenId.
        */
        require(
            noOneMarried(_fiances),
            "One of the fiances is already married"
        );

        // associate the wedding contract address with the fiances
        // if a fianec got divorced earlier, the address of the canceled contract will be overwritten
        for (uint32 i = 0; i < _fiances.length; i++) {
            fianceAddressToWeddingContract[_fiances[i]] = msg.sender;
        }

        uint256 tokenId = totalSupply();
        _mint(msg.sender, tokenId);
        // since the task description does not specify what data should be stored in the token, we just added this dummy data to show that we know how to do it
        tokenURIs[
            tokenId
        ] = "Here we can add arbitrary data to the token. For example a link to some off chain data.";

        emit WeddingCertificateIssued(_fiances);
    }

    function burnWeddingCertificate() external onlyDeployedContracts {
        /* Burns the wedding certificate of the calling wedding contract.
        This function can only be called by a deployed wedding contract. This ensures that
        the wedding was divorced in the correct way.
        The association of address to wedding contract address will stay but the balance of the
        wedding contract address will be 0. 
        Also the isMarried function will return false for the fiances after this function was called
        by the wedding contract.
        */
        _burn(tokenOfOwnerByIndex(msg.sender, 0));

        emit WeddingCertificateBurned(msg.sender);
    }

    function getMyWeddingTokenId() external view onlyMarried returns (uint256) {
        /*Once a person (or its adddress) got married, the address of the wedding contract
        is associated with the address of the person and the wedding contract gets set as the owner
        of the wedding token. This function returns the wedding token id of the wedding token
        address of the calling address.
        This function requires that the calling address is married. Otherwise it will raise an error.
        */
        return
            tokenOfOwnerByIndex(fianceAddressToWeddingContract[msg.sender], 0);
    }

    function getMyWeddingContractAddress()
        external
        view
        onlyMarried
        returns (address)
    {
        /*Once a person (or its adddress) got married, the address of the wedding contract
        is associated with the address of the person. This function returns the address of the
        wedding contract of the calling address.
        Even if a weddding got divorced this function will return the address of the canceled
        wedding contract. However the balance of the wedding contract will be 0 and the 
        isCanceled flag of the wedding contract will be true.
        If a divorced person marries again, the address of the new wedding contract will be
        associated with the address of the person.
        */
        return fianceAddressToWeddingContract[msg.sender];
    }
}
