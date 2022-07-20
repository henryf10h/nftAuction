// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@uniswap/contracts/libraries/TransferHelper.sol";

contract EnglishAction is Ownable, ReentrancyGuard {

    IERC721 public nft;
    uint256 public nftId;
    address payable public seller;
    enum State{open, closed}
    State public state;
    uint256 public fee;
    uint256 public initBid;
    uint256 public auctionEnds;
    uint256 public highestBid;
    address public highestBidder;
    mapping(address => uint256) public bids;
    mapping(address => uint256) public balance;

    constructor(){

        state = State.closed;
    }

// what if seller never calls start()? you would be forced to deploy another contract.
// use emergencyWithdraw()

    function start() external {
        require(state == State.closed,"state must be closed");
        require(msg.sender == seller,"you are not allowed to start the lottery");
        //nft.approve(address(this),nftId);//https://stackoverflow.com/questions/69751069/how-to-transfer-an-erc721-token
        nft.transferFrom(msg.sender, address(this),nftId);
        state = State.open;
        //todo
        // emit started();
    }

// lottery could be open, but time has passed. Now lottery is open and emergencywithdraw can't be called. >> call end()

    function bid() external payable {
        require(state == State.open,"state must be open");
        require(msg.value > highestBid, "you need higher bid");
        require(block.timestamp < auctionEnds, "auction is ended");
        if (highestBidder == address(0)) {
            //first time bid is called, because we set highestBidder to 0 after the auction
            highestBidder = msg.sender;
        } else{
            // we need to store last bidders, so they can withdraw latter
            bids[highestBidder] += highestBid;
            highestBidder = msg.sender;
        }
        highestBid = msg.value;
        //todo 
        // emit bid()
    }

    function end() external {
        require(msg.sender == seller || msg.sender == owner(),"Is not owner nor seller.");
        require(state == State.open,"Lottery is not open.");
        require(block.timestamp > auctionEnds,"Lottery has not ended.");
        state = State.closed;
        if (highestBidder == address(0)) {
            nft.transferFrom(address(this),seller,nftId);
        } else{
            nft.transferFrom(address(this),highestBidder,nftId);
            uint256 total = highestBid;
            uint256 amtOwner = (total * fee) / 10000;
            uint256 amtWinner = (total - amtOwner);
            balance[owner()] += amtOwner;
            balance[seller] += amtWinner;
        }
        delete highestBid;
        delete highestBidder;
        delete auctionEnds;
        //todo 
        // emit end()
    }

// there was a bug in withdraw fuction.
// Before, highestbidder could've withdrawn and the state  would've not been set to zero after.
// hisghestbidder could have bid the highest, then withdraw, wait for auction to end and receive the nft.
// highest bidder can not withdraw

    function withdraw() external nonReentrant {
        require(bids[msg.sender] > 0, "You have no funds.");
        if (msg.sender != highestBidder) {
            uint256 amt = bids[msg.sender];
            bids[msg.sender] = 0;
            TransferHelper.safeTransferETH(msg.sender,amt);
            //todo 
            // emit withdraw()
        }
        

    }

    function claim() external nonReentrant{
        require(balance[msg.sender] > 0, "You have no funds.");
        uint256 amt = balance[msg.sender];
        balance[msg.sender] = 0;
        TransferHelper.safeTransferETH(msg.sender,amt);
        //todo
        // emit claim()
    }

    function setup(address payable _seller, uint256 _hoursDuration, uint256 _initBid, IERC721 _nftContract, uint256 _nftId, uint256 _fee) external onlyOwner {
        require(state == State.closed,"state must be closed");
        require(auctionEnds == 0,"you can not setup while auction is runnig");
        seller = _seller;
        auctionEnds = block.timestamp + _hoursDuration; // time in blocks e.g. 1 block = 1 seg
        initBid = _initBid; // e.g. 10**18 matic
        nft = IERC721(_nftContract); 
        nftId = _nftId;
        fee = _fee; // 100 = 10 basis points 

    }

//In case seller never calls start(), here we can reset and then we will be able to call setup()

    function emergencyReset() external onlyOwner() {
        require(block.timestamp > auctionEnds,"auction has not ended");
        require(state == State.closed,"state must be closed");
        delete auctionEnds;
    }

}
