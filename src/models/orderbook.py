import heapq
import mongoengine as me
import models.items
from functools import total_ordering
from bisect import insort

@total_ordering
class Order(me.Document):
    item = me.ReferenceField(models.items.Item)
    user = me.ReferenceField(models.users.User)
    price = me.IntField(required = True)
    quantity = me.IntField(required = True)
    type = me.StringField(choices=['bid','ask'])
    state = me.StringField(choices=['outstanding','filled','completed'])

    @property
    def bid(self):
        return self.type == "bid"
    @property
    def open_qty(self):
        return self.quantity - self.filled
    @property
    def is_filled(self):
        print self.filled, self.quantity
        return self.filled == self.quantity
    _sortp = None
    @property
    def sort_price(self):
        if self._sortp is None:
            self._sortp = self.price if not self.price == 0 else (
            -1 if self.bid else 0)
        return self._sortp
    def fill(self, qty, cross_price):
        self.filled += qty
        self.cross_price = cross_price
        if self.bid:
            return self.user.buy(self.item, qty, qty*(self.price-cross_price))
        else:
            return self.user.sell(self.item, qty, cross_price*qty)
    def matches(self, current):
        if self.bid:
            if self.sort_price < current.sort_price:
                return False
        else:
            if self.sort_price > current.sort_price:
                return False
        return True
    def __eq__(self, other):
        return self.sort_price == other.sort_price
    def __lt__(self, other):
        if not self.bid:    # This is a hack, but I think it works?
            return self.sort_price < other.sort_price
        else:
            return self.sort_price > other.sort_price

    def __str__(self):
        return "<{} {} @ {}>".format("Bid" if self.bid else "Ask", self.open_qty, self.price)
    def __repr__(self):
        return self.__str__()

class OrderBook(me.Document):
    """Represents and orderbook for a ROTMG item. 
    Contains a list of bid and sell offers, as well as methods for determining a price level."""
    
    def __init__(self, *args, **kwargs):
        super(OrderBook, self).__init__(*args, **kwargs)
        self.asks = sorted(self.asks)
        self.bids = sorted(self.bids)

    key = me.StringField(
            primary_key = True,
            unique = True,
            required = True
        )

    def clean(self):
        [i.save() for i in self.asks]
        [i.save() for i in self.bids]

    asks = me.ListField(me.ReferenceField(Order))
    bids = me.ListField(me.ReferenceField(Order))

    @property
    def price(self):
        if 0 in (len(self.asks), len(self.bids)): return (0.0, 0.0, 0.0) #or len(self.bids) == 0
        return self.asks[0].price, self.asks[0].price, self.bids[0].price
        # return (self.asks[0].price + self.bids[0].price)/2.0, self.asks[0].price, self.bids[0].price

    # add an order to book
    # order the order to add
    # conditions special conditions on the order
    # true if the add resulted in a fill
    # virtual bool add(const OrderPtr& order, OrderConditions conditions = 0);
    def add(self, order):
        matched = False
        # Validate?
        if order.bid:
            matched = self._match_bid(order)
        else:
            matched = self._match_ask(order)
        if order.open_qty > 0:
            if order.bid:
                insort(self.bids, order)
            else:
                insort(self.asks, order)
        return matched

    # cancel an order in the book
    # virtual void cancel(const OrderPtr& order);
    def cancel(self, order):
        pass

    # match a new ask to current bids
    # inbound_order the inbound order
    # inbound_price price of the inbound order
    # bids current bids
    # true if a match occurred 
    # virtual bool match_order(Tracker& inbound_order, 
    #                        const Price& inbound_price, 
    #                        Bids& bids);
    def _match_ask(self, inbound):
        matched = False
        for bid in self.bids[:]:
            if inbound.matches(bid):
                matched = True
                self._cross_orders(inbound, bid)
                if bid.is_filled:
                    bid.save()
                    self.bids.remove(bid)
                if inbound.is_filled:
                    inbound.save()
                    break
            elif bid < inbound:
                break
        return matched

    # match a new bid to current asks
    # inbound_order the inbound order
    # inbound_price price of the inbound order
    # asks current asks
    # true if a match occurred 
    # virtual bool match_order(Tracker& inbound_order, 
    #                        const Price& inbound_price, 
    #                        Asks& asks);
    def _match_bid(self, inbound):
        matched = False
        for ask in self.asks[:]:
            if inbound.matches(ask):
                matched = True
                self._cross_orders(inbound, ask)
                if ask.is_filled:
                    ask.save()
                    self.asks.remove(ask)
                if inbound.is_filled:
                    inbound.save()
                    break
            elif ask > inbound:
                break
        return matched
    
    # perform fill on two orders
    # inbound_tracker the new (or changed) order tracker
    # current_tracker the current order tracker
    # void cross_orders(Tracker& inbound_tracker, 
    #                 Tracker& current_tracker);
    def _cross_orders(self, inbound_order, current_order):
        fill_qty = min(inbound_order.open_qty, current_order.open_qty)
        cross_price = current_order.price
        if cross_price == 0:
            cross_price = inbound_order.price
        print "cross", inbound_order, current_order
        print 'current:',current_order.price,"inbound",inbound_order.price
        print inbound_order.fill(fill_qty, cross_price)
        print current_order.fill(fill_qty, cross_price)

    # # find a bid
    # # void find_bid(const OrderPtr& order, typename Bids::iterator& result);
    # def _find_bid(order):
    #     pass

    # # find an ask
    # # void find_ask(const OrderPtr& order, typename Asks::iterator& result);
    # def _find_ask(order):
    #     pass

    # match an inbound with a current order
    # virtual bool matches(const Tracker& inbound_order, 
    #                    const Price& inbound_price, 
    #                    const Quantity inbound_open_qty,
    #                    const Tracker& current_order,
    #                    const Price& current_price,
    #                    bool inbound_is_bid);
    
    ##
    ## Moved to Order.matches()
    ##

def from_items():
    from models.items import Item
    for i in Item.objects:
        OrderBook(key=i.key).save()

def clear():
    from models.users import User
    for i in OrderBook.objects:
        i.asks = []
        i.bids = []
        i.save()
    for i in User.objects:
        i.orders = []
        i.save()
    Order.objects.delete()