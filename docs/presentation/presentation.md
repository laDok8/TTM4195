# Presentation
## Outline
- High level design overview (Moritz) 
    - 2 Contracts
        - Registry: for keeping track of all weddings
        - WeddingContract: to manage the wedding procedure
    - Factory contract pattern
        - Separation of concerns
        - No expensive lookups
        - Every wedding is a contract
    - Proxy contract pattern
        - Cheaper deployment of wedding contracts
        - implementation is only deployed once
        - deployment cost wedding contract:1.5M vs deployment cost proxy contract:250k
            - still expensive but okay
    - Polygamous
- Registry details (Lada)
    - ERC721
    - is the contract factory
    - Mechanism to NFT store data on the blockchain
    - no use of ERC721URIStorage
- WeddingContract details (Jonathan)
    - Proxies to lower deployment costs
    - Upgradeable implementation
    - Wedding procedure
- Development (Moritz)
    - How can automated tests be written? --> Brownie
    - Brownie provides python interface to deployed contracts
    - python testing frameworks can be used
    - bockchain is simulated but time can be manipulated
- Poblems and Challenges
    - checking wethether someone is married
    - reducing gas costs --> Proxies
    - problem with polygamy: all cases had to be handled generally
        - 2 out of N ?
    - on testchain no return value is returned for non-view functions
        - workaround: use of events
- Repeat: Stesp of the wedding procedure
- Demo (Espen)




    
    
    
    - gas costs
    - advantages
        - implementation exhachangable
        - 
- development
- test run
    - show outline image
- problems