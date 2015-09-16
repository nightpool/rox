import flask
from flask import Flask
import mongoengine
import models.items

class LocalFlask(Flask):
    jinja_options = {
        "extensions": ['jinja2.ext.autoescape', 'jinja2.ext.with_'],
        "trim_blocks": True,
        "lstrip_blocks": True
    }

app = LocalFlask(__name__)

app.secret_key = open("secret").read()
mongoengine.connect("rox")

@app.route("/")
def index():
    return flask.render_template("index.html")

@app.route("/test")
def test():
  flask.flash("test test 1")
  flask.flash("Test test 2")
  return flask.redirect('/')

# @app.route("/items")
# def items():
#     return flask.render_template("items.html", items=models.items.Item.objects)

from views import users, exchange
app.register_blueprint(users.view)
app.register_blueprint(exchange.view)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
