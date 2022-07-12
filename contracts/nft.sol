// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract NFt is ERC721 {
    
    constructor()ERC721("myNft", "nft"){}
    
    function mintNft() external {
        _safeMint(msg.sender,67);
    }
}