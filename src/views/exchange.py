import flask
import wtforms as wtf
from models import orderbook, items, users
from werkzeug.datastructures import MultiDict

view = flask.Blueprint("exchange", __name__)

@view.route("/orders/<item>")
def view_orders(item):
    book = orderbook.OrderBook.objects.with_id(item)
    item = items.Item.objects.with_id(item)
    if book is None:
        flask.abort(404)
    return flask.render_template("book.html", book=book, item=item)

@view.route("/items")
def items_v():
    books = [(i, orderbook.OrderBook.objects.with_id(i.key)) for i in items.Item.objects]
    return flask.render_template("items.html", books=books)

class OrderForm(wtf.Form):
    type = wtf.SelectField("Type", choices = [('bid',"Buy"), ('ask',"Sell")])
    item = wtf.SelectField("Item", choices = [(i.key, i.name) for i in items.Item.objects])
    quantity = wtf.IntegerField("Quantity", [wtf.validators.NumberRange(min=0)])
    price = wtf.IntegerField("Price", [wtf.validators.NumberRange(min=0)])
@view.route("/order", methods=['GET','POST'])
def new_order():
    args = MultiDict()
    args.update(flask.request.form)
    if flask.request.method == "GET":
        args.update(flask.request.args)
    form = OrderForm(args)
    if flask.request.method == "POST" and form.validate():
        if 'login' not in flask.session:
            flask.flash("You need to be logged in to place an order")
            return flask.redirect("/user/login")
        print form.item.data
        user = users.User.objects.with_id(flask.session['login'])
        order = orderbook.Order(user = user, item=items.Item.objects.with_id(form.item.data),
            quantity = form.quantity.data, price = form.price.data, type=form.type.data)
        order.save()
        user.orders.append(order)
        user.save()
        book = orderbook.OrderBook.objects.with_id(form.item.data)
        result = book.add(order)
        book.save()
        print "{} order {} by user {} got result {}".format(book.key, order, user.name, result)
        return flask.redirect("/user/{}".format(user.name))
    return flask.render_template("form.html", form=form)