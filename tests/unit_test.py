import pytest
import brownie
from brownie import accounts, config, network, EnglishAction, chain, NFt
import time


@pytest.fixture
def auction(accounts):
    return accounts[0].deploy(EnglishAction)

@pytest.fixture
def nft(accounts):
    return accounts[1].deploy(NFt)

# https://stackoverflow.com/questions/70370224/problems-using-ganache-cli-command

#when calling setup, state must be closed
def test_setup_state_closed(auction,nft):
    auction = EnglishAction[len(EnglishAction) - 1]
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    assert auction.state() != 0

#auction was successfully setup
def test_setup_auction_ends(auction,nft):
    auction = EnglishAction[len(EnglishAction) - 1]
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    #TypeError: int() argument must be a string, a bytes-like object or a number. Because we typed chain.time instead of chain.time()
    assert auction.auctionEnds() > chain.time()

#setup caller is not owner
def test_setup_not_owner_call(auction,nft):
    with brownie.reverts():
        auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[1] })

#if auction was not setup, then nobody can call start()
def test_start_without_setup(auction):
    with brownie.reverts("you are not allowed to start the lottery"):
        auction.start({'from': accounts[0] })

#mint nft and verify owner
def test_mint_nft(nft):
    nft.mintNft({'from': accounts[1] })
    assert nft.ownerOf(67) == accounts[1]

#verify if auction address is approved
def test_is_nft_approved(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    assert nft.getApproved(67) == auction

#verify if state of auction is open after calling start()
def test_auction_state_after_start(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    assert auction.state() == 0

#verify if bid() reverts when state is not open
def test_state_bid(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    with brownie.reverts("state must be open"):
        auction.bid({'from':accounts[2],'amount' :1000000000000000000})

# auction must revert when bid is not enough
def test_value_reverts_bid(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    with brownie.reverts("you need higher bid"):
        auction.bid({'from':accounts[2],'amount' :0})

# auction must revert when time has ended
def test_auction_ended_reverts(auction,nft):
    auction.setup(accounts[1],0,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    with brownie.reverts("auction is ended"):
        auction.bid({'from':accounts[2],'amount' :1000000000000000000})

#assert highest bidder is last bidding acount
def test_auction_highest_bidder(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[2],'amount' :1000000000000000000})
    assert auction.highestBidder() == accounts[2]

#assert that highest bid is the last successful bid()
def test_auction_highest_bid(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[2],'amount' :1000000000000000000})
    assert auction.highestBid() == 1000000000000000000

#require seller or owner to end the auction
def test_auction_end_caller(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[2],'amount' :1000000000000000000})
    with brownie.reverts("Is not owner nor seller."):
        auction.end({'from':accounts[2]})

#state must be open when calling end()
def test_auction_state_before_end(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    with brownie.reverts("Lottery is not open."):
        auction.end({'from':accounts[0]})

#reverts if auction time has not ended
def test_auction_time_not_ended(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[2],'amount' :1000000000000000000})
    with brownie.reverts("Lottery has not ended."):
        auction.end({'from':accounts[0]})

#assert that state is changed to open after bidding
def test_auction_state_open(auction,nft):
    auction.setup(accounts[1],300,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[2],'amount' :1000000000000000000})
    assert auction.state() == 0

#assert that owner is seller if nobody bids 
def test_auction_highest_bid(auction,nft):
    auction.setup(accounts[1],0,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.end({'from': accounts[1] })
    assert nft.ownerOf(67) == accounts[1]

#assert that owner is hishest bidder 
def test_auction_highest_bidder_after_end(auction,nft):
    auction.setup(accounts[1],3,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[2],'amount' :1000000000000000000})
    time.sleep(3)
    auction.end({'from': accounts[1] })
    assert nft.ownerOf(67) == accounts[2]

#assert highest bid is the last bidder's amount
def test_auction_highest_bid_highest_bidder(auction,nft):
    auction.setup(accounts[1],5,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[3],'amount' :1000000000000000000})
    assert auction.highestBid() == 1000000000000000000

#highest bid,bidder and auction time should be reset to zero.
def test_states_after_auction_end(auction,nft):
    account0 =accounts.at('0x0000000000000000000000000000000000000000', force=True)
    auction.setup(accounts[1],3,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[3],'amount' :1000000000000000000})
    time.sleep(3)
    auction.end({'from': accounts[1] })
    assert auction.highestBid() == 0
    assert auction.highestBidder() == account0
    assert auction.auctionEnds() == 0

#withdraw requires to have funds >>>  brownie test tests/test_transfer.py
def test_need_funds_to_withdraw(auction,nft):
    auction.setup(accounts[1],3,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[4],'amount' :1000000000000000000})
    time.sleep(3)
    auction.end({'from': accounts[1] })
    with brownie.reverts("You have no funds."):
        auction.withdraw({'from':accounts[3]})

#claim requires to have funds >>>  brownie test tests/test_transfer.py
def test_need_funds_to_claim(auction,nft):
    auction.setup(accounts[1],3,1000000000000000000,nft,67,500,{'from': accounts[0] })
    nft.mintNft({'from': accounts[1] })
    nft.approve(auction,67,{'from': accounts[1] })
    auction.start({'from': accounts[1] })
    auction.bid({'from':accounts[4],'amount' :1000000000000000000})
    time.sleep(3)
    auction.end({'from': accounts[1] })
    with brownie.reverts("You have no funds."):
        auction.claim({'from':accounts[3]})

#only can call when auction time has passed
def test_emergency_reset(auction,nft):
    auction.setup(accounts[1],2,1000000000000000000,nft,67,500,{'from': accounts[0] })
    with brownie.reverts("auction has not ended"):
        auction.emergencyReset({'from':accounts[0]})

