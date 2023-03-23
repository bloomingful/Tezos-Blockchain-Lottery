# BLOOMING DAN A. MONEDA

import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(5),
            max_tickets = sp.nat(5),
            operator = sp.test_account("admin").address,
        )
    
    @sp.entry_point
    def buy_ticket(self, number_tickets): # we added a new parameter to specify number of tickets to buy for each transaction
        sp.set_type(number_tickets, sp.TNat) # we specified that this param is of type nat

        # Sanity checks
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(number_tickets > 0, "MUST BUY AT LEAST 1 TICKET") # we verified whether the number of tickets to buy is at least 1, else, throw an error
        sp.verify(sp.amount >= self.data.ticket_cost, "INVALID AMOUNT")

        # Storage updates
        sp.for x in sp.range(0, number_tickets, step = 1):
            self.data.players[sp.len(self.data.players)] = sp.sender # for loop to continuously execute depending on the number of tickets bought
            self.data.tickets_available = sp.as_nat(self.data.tickets_available - 1)

        # Return extra tez balance to the sender
        extra_balance = sp.amount - sp.split_tokens(self.data.ticket_cost, number_tickets, sp.nat(1)) # extra_balance now considers how many tickets are bought to be multiplied to the cost of each ticket to find the total cost
        sp.if extra_balance > sp.tez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def modify_ticket_cost(self, new_ticket_cost):
        sp.set_type(new_ticket_cost, sp.TMutez)
        
        # Sanity checks
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME IS YET TO END")

        # Change ticket cost
        self.data.ticket_cost = new_ticket_cost

    @sp.entry_point
    def modify_max_tickets(self, new_max_tickets):
        sp.set_type(new_max_tickets, sp.TNat)
        
        # Sanity checks
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME IS YET TO END")

        # Change max tickets
        self.data.max_tickets = new_max_tickets
        self.data.tickets_available = new_max_tickets # remember that we also have to modify the tickets available value to reflect to the max tickets
        
    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")

@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")
    john = sp.test_account("john")

    # Contract instance
    lottery = Lottery()
    scenario += lottery

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(7), sender = alice)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = bob)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(3), sender = john)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(21).run(sender = admin)

    # modify_ticket_cost
    scenario.h2("modify_ticket_cost (valid test)")
    scenario += lottery.modify_ticket_cost(sp.tez(2)).run(sender = admin)

    scenario.h2("modify_ticket_cost (failure test)")
    scenario += lottery.modify_ticket_cost(sp.tez(2)).run(sender = alice, valid = False)
    
    # modify_max_tickets
    scenario.h2("modify_max_tickets (valid test)")
    scenario += lottery.modify_max_tickets(10).run(sender = admin)

    scenario.h2("modify_max_tickets (failure test)")
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(5), sender = alice)
    scenario += lottery.modify_max_tickets(10).run(sender = admin, valid = False)
