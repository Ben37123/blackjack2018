from player import Player
from hand import Hand
from shoe import Shoe
from toolbox import is_number
from table import Table

class Dealer(Player):

    def __init__(self, name, money):
        super().__init__('Bob the dealer', 1000000)
        self._playingPlayers = []
        self._playersWithInsurance = []
        self._shoe = Shoe()

    def sit(self, table):
        """Override the player sit method. so that the dealer sits on the right side of the table."""
        if type(table) == Table:
            self._table = table
            table.add_dealer(self)
        else:
            raise TypeError('Table parameter must be of type Table.')

    def bet_or_leave(self):
        """
        At the start of each round the player can either bet by entering an amount
        to bet, sit this hand out by entering 0 for a bet, or leave the table by
        entering -1.
        """
        #
        # The dealer will not be in the list of players, so this method will not be
        # called on the dealer.
        #
        pass

    def want_insurance(self):
        """
        Returns True if the player should buy insurance else return False.

        This procedure is called by the dealer after all players have bet and
        receives their cards and after the dealer has received his cards. It is
        only called if the dealer is showing an ace (the dealer might have blackjack).
        """
        #
        # The dealer will not be in the list of players, so this method will not be
        # called on the dealer.
        #
        pass

    def play(self, hand, dealerShowing):
        """
        Returns the player's action for this hand. The dealer calls this method
        repeatedly for each of the player's hands until all hands are completed.
        Valid return values are listed below. Note that two values are returned:

        choice: one of the plays listeded below
        additionalBet: the amount to "double down" by

        additionalBet is discarded by the caller in all other cases.

        allPlays = {'s': '[S]tand',
                    'h': '[H]it',
                    'd': '[D]ouble down',
                    'p': 's[P]lit',
                    'u': 's[U]rrender'}
        return choice, additionalBet
        """
        if hand.value() < 17:
            choice = 'h' #hit
        else:
            choice = 's' #stand
        additionalBet = None
        return choice, additionalBet

    def take_bets(self):
        self._playingPlayers = []
        leavingPlayers = []
        for player in self._table.players:
            #
            # = -1: player is leaving the table
            # =  0: players is sitting this hand out
            # >  0: player is betting this amount
            #
            betAmount = player.bet_or_leave()
            name = player.name.capitalize()
            if betAmount == -1:  # leaving table
                leavingPlayers.append(player)
                print(f"{name} is leaving the table with ${player.money:0.2f}.")
            elif betAmount == 0:
                print(f"{name} is sitting this hand out.")
            elif betAmount > 0 and player.money > betAmount:
                self._playingPlayers.append(player)
                player.rake_out(betAmount)
                self.rake_in(betAmount)
                player.add_hand(Hand(betAmount))
                print(f"{name} is betting ${betAmount:0.2f}.")
            else:
                print(f"{name} doesn't have enough money to bet ${betAmount:0.2f}. Sitting this hand out.")
            for player in leavingPlayers:
                self._table.leave_table(player)
                print(f"playing players: {self._playingPlayers}")

    def show_card_to_players(self, card):
        """
        Make sure that players who might be counting cards get to see
        every card that is delt, not just the ones in their hands.
        """
        for player in self._playingPlayers:
            player.count(card)

    def deal(self):
        """
        Deal an initial 2 cards to each player and to the dealer.
        """
        #
        # Shuffle the cards if we need to.
        #
        if self._shoe.should_shuffle():
            self._shoe.shuffle()
            for player in self._playingPlayers:
                player.reset_count()
        #
        # Deal cards to each player.
        #
        cardsToDeal = 2
        for _ in range(cardsToDeal):
            for player in self._playingPlayers:
                card = self._shoe.draw().flip()
                player.hands[0].hit(card)
                self.show_card_to_players(card)

        #
        # Deal yourself some cards. It doesn't matter what we
        # bet here, because we are not actually ever paying out
        # or changing the dealer's money. So let's bet pi. That
        # way we will know the dealer by his bet.
        #
        bet = 3.1415
        self.add_hand(Hand(bet))
        card = self._shoe.draw().flip()
        #TODO remove this debugging code
#        print('shoe:', self._shoe)
#        print('draw test:', self._shoe.draw())
#        print('flip test:', self._shoe.draw().flip())
#        print('card:', card)
        self.hands[0].hit(card)
        self.show_card_to_players(card)
        self.hands[0].hit(self._shoe.draw().flip())

    def offer_insurance(self):
        self._playersWithInsurance = []
        if self.hands[0][1].name == 'ace':
            for player in self._playingPlayers:
                if player.wants_insurance():
                    self._playersWithInsurance.append(player)

    def play_hands(self, whichPlayers = None):
        if whichPlayers == None:
            whichPlayers = self._playingPlayers
        dealerShowing = self.hands[0][1]
        for player in whichPlayers:
            for hand in player.hands:
                while hand.can_hit():
                    playerDecision, additionalBet = player.play(hand,dealerShowing)
                    #
                    # [S]tand
                    #
                    if playerDecision == 's':
                        hand.stand()
                    #
                    # [H]it
                    #
                    elif playerDecision == 'h':
                        card = self._shoe.draw().flip()
                        self.show_card_to_players(card)
                        hand.hit(card)
                    #
                    # s[P]lit
                    #
                    elif playerDecision == 'p':
                        if hand.can_split() and player.money >= hand.bet:
                            self.rake_in(player.rake_out(hand.bet))
                            newHand = Hand(hand.bet).hit(hand.split())
                            card = self._shoe.draw().flip()
                            self.show_card_to_players(card)
                            newHand.hit(card)
                            player.add_hand(newHand)
                            card = self._shoe.draw().flip()
                            self.show_card_to_players(card)
                            hand.hit(card)
                        else:
                            print("Sorry, you can't split this hand (pick again).")
                    #
                    # [D]ouble down
                    #
                    elif playerDecision == 'd':
                        if hand.can_double() and is_number(additionalBet) and player.money >= additionalBet:
                            card = self._shoe.draw().flip()
                            self.show_card_to_players(card)
                            hand.double_down(card, additionalBet)
                            self.rake_in(player.rake_out(additionalBet))
                        else:
                            print("Sorry, you can't double this hand (pick again).")
                    #
                    # s[U]rrender
                    #
                    elif playerDecision == 'u':
                        print('Sorry, surrender is not implemented (pick again).')
                    #
                    # [A]nything else
                    #
                    else:
                        print(f"I'm sorry, I don't know what '{playerDecision}' means.")

    def play_own_hand(self):
        #
        # Show the dealer's hole card to everyone. This allows players who
        # are counting cards to include the dealer's hole card in their count.
        #
        holeCard = self.hands[0][1]
        self.show_card_to_players(holeCard)
        self.play_hands([self])

    def payout_hands(self):
        dealerHand = self.hands[0]
        for player in self._playingPlayers:
            for hand in player.hands:
                if hand.isBusted:
                    winnings = 0
                elif hand.isBlackJack and not dealerHand.isBlackJack:
                    winnings = hand.bet * 3
                elif hand.isBlackJack and dealerHand.isBlackJack:
                    winnings = hand.bet
                elif not hand.isBlackJack and dealerHand.isBlackJack:
                    winnings = 0
                elif hand.value() == dealerHand.value():
                    winnings = hand.bet
                elif dealerHand.isBusted:
                    winnings = hand.bet * 2
                elif hand.value() > dealerHand.value():
                    winnings = hand.bet * 2
                player.rake_in(winnings)
                self.rake_out(winnings)
                print(f"{player.name} won ${winnings:02f} on {hand}.")
        if dealerHand.isBlackJack:
            for player in self._playersWithInsurance:
                winnings = player.hands[0].bet * 2
                player.rake_in(winnings)
                self.rake_out(winnings)
                print(f"{player.name} won ${winnings:02f} on the insurance bet.")
        for player in self._playingPlayers:
            player.discard_hands()
        self.discard_hands()





