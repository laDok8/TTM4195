# Weeding SC
## Concept
- for each wedding a increasing id is assigned, a wedding does not need to be successful
- for all weddings which ever are created the values are stored in mappings with the id as key --> each relevant value for a wedding is saved as a mapping from the wedding id to the value 
- one of the value mappings contain the token issued in case of a successful wedding
- another mapping is used to map addresses to their currently active wedding id
- if a wedding id is associated with an address, the person is either engaged or wed
- if a wedding is cancelled (due to vote or engagementRevoke) the wedding id is deleted from the address mapping for all fiances. The same happens if a wedding is cancelled afterwards.