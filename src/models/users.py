import mongoengine as me
from passlib.context import CryptContext

import models.items

pwd_context = CryptContext(
    schemes=["sha512_crypt"],
    default="sha512_crypt",
    all__vary_rounds=0.1
)

class User(me.Document):

    name = me.StringField( primary_key = True,
            unique = True,
            required = True)
    password_hash = me.StringField(required = True)
    email = me.StringField(required = True)
    # email_confirmed = me.BooleanField()
    # confirm_token = me.StringField()

    balance = me.IntField()
    inventory = me.MapField(me.IntField(default=0))

    orders = me.ListField(me.ReferenceField("Order"))
    # successful = me.ListField(me.DictField())

    def passwd(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def auth(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_new_inventory(self):
        self.inventory = {'serpentine_staff': 2, 'fire_spray_spell': 1}
        self.balance = 200
        self.save()

    @property
    def item_inv(self):
        return {models.items.Item.objects.with_id(k) : v for k, v in self.inventory.iteritems()}
 
    @property
    def past_orders(self):
        return [i for i in self.orders if i.is_past]

    @property
    def successful_orders(self):
        return [i for i in self.orders if i.is_pending_user]

    @property
    def current_orders(self):
        return [i for i in self.orders if i.is_outstanding]        

    def successful_bid(self, item, quantity, refund=0):
        q = self.inventory.get(item.key, 0) + quantity
        self.inventory[item.key] = quantity
        self.balance += refund
        # self.successful.append({'item': item, 'quantity': quantity, 'refund': refund})
        print {'item': item, 'quantity': quantity, 'refund': refund}
        self.save()

    def successful_ask(self, item, quantity, price):
        self.balance += price
        q = self.inventory.get(item.key, 0) - quantity
        self.inventory[item.key] = quantity
        if self.inventory[item.key]:
            del self.inventory[item.key]
        # self.successful.append({'item': item, 'quantity': quantity, 'price': price})
        print {'item': item, 'quantity': quantity, 'price': price}
        self.save()
