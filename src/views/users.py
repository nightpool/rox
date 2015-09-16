import flask
import wtforms as wtf
from models.users import User
from models.items import Item
from werkzeug.datastructures import MultiDict

view = flask.Blueprint("users", __name__, url_prefix="/user")

class LoginForm(wtf.Form):
    name = wtf.StringField("Username")
    password = wtf.PasswordField("Password")
@view.route('/login', methods=["GET","POST"])
def login():
    form = LoginForm(flask.request.form)
    if flask.request.method == "POST" and form.validate():
        user = User.objects.with_id(form.data['name'])
        if user.auth(form.data['password']):
            flask.session['login'] = user.name
            flask.flash("Login successful!")
            return flask.redirect(flask.url_for('.single_user', name=user.name))
        else:
            flask.flash("Bad Login","error")
    return flask.render_template("login.html", form=form)

@view.route('/logout', methods=["GET"])
def logout():
    del flask.session['login']
    flask.flash("Logged out")
    return flask.redirect('/')

class SignupForm(wtf.Form):
    name = wtf.StringField("Username")
    password = wtf.PasswordField("Password", [wtf.validators.Length(min=5)])
    email = wtf.StringField("Email", [wtf.validators.Email()])

    def validate_name(self, field):
        if User.objects.with_id(field.data) is not None:
            raise wtf.ValidationError("User exists")

@view.route('/signup', methods=["GET","POST"])
def signup():
    form = SignupForm(flask.request.form)
    if flask.request.method == "POST" and form.validate():
            user = User(**form.data)
            user.passwd(form.data['password'])
            user.generate_new_inventory()
            user.save()

            flask.session['login'] = user.name
            flask.flash("Signup successful!")
            print flask.url_for('.single_user', name=user.name)
            return flask.redirect(flask.url_for('.single_user', name=user.name))
    return flask.render_template("signup.html", form=form)

class CheatForm(wtf.Form):
    name = wtf.StringField("Username")
    item = wtf.SelectField("item", choices = [(i.key, i.name) for i in Item.objects], default=('',''))
    quantity = wtf.IntegerField("quantity", default = 0)
    coin = wtf.IntegerField("add coin", default = 0)
    def validate_name(self, field):
        return User.objects.with_id(field.data) is not None
@view.route('/cheat', methods=["GET","POST"])
def cheat():
    args = MultiDict()
    args.update(flask.request.form)
    if flask.request.method == "GET":
        args.update(flask.request.args)
    form = CheatForm(args)
    if flask.request.method == "POST" and form.validate():
        user = User.objects.with_id(form.name.data)
        m = False
        if form.item.data and form.quantity.data:
            m = True
            q = user.inventory.get(form.item.data, 0) + form.quantity.data
            user.inventory[form.item.data] = q
            flask.flash("Added {} item{}".format(form.quantity.data, 
                    "s" if form.quantity.data > 1 else ""))
        if form.coin.data:
            m = True
            user.balance += form.coin.data
            flask.flash("Added {} coin{}".format(form.coin.data, 
                    "s" if form.coin.data > 1 else ""))
        if not m:
            flask.flash("No changes made!","error")
        else:
            user.save()
            return flask.redirect(flask.url_for(".single_user", name=user.name))
    return flask.render_template("form.html", form=form)

@view.route('/all')
def users():
    return flask.render_template("users.html", users=User.objects)

@view.route('/<name>')
def single_user(name):
    u = User.objects.with_id(name)
    logged_in = 'login' in flask.session and flask.session['login'] == name
    if u is None:
        flask.abort(404)
    return flask.render_template("user.html", user=u, logged_in=logged_in)