import string

from flask_sqlalchemy import SQLAlchemy
from random import choice
from werkzeug.security import generate_password_hash



db = SQLAlchemy()


class User(db.Model):
    """
    Class for describe user ORM table model.
    For Login and register user in system.
    
    """
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(128), unique=True)
    email = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    apiid = db.Column(db.String(32))

    def __init__(self, username, email, password):
        self.user_name = username.lower()
        self.email = email.lower()
        self.password = generate_password_hash(password)
        self.apiid = self.gen_api_id()

    @staticmethod
    def gen_api_id():
        api_id = ''.join(choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits)
            for x in range(31))

        return api_id

    def as_json(self):
        j_data = {"id": self.user_id,
                  "name": self.user_name,
                  "email": self.email,
                  "password": self.password,
                  "api_key": self.apiid}

        return j_data


class Currency(db.Model):
    """
    Class for describe Currency ORM table model.
    
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    symbol = db.Column(db.String(6))

    def __init__(self, name, symbol):
        self.name = name.lower()
        self.symbol = symbol.upper()

    def as_json(self):
        j_data = {"id": self.id,
                  "name": self.name,
                  "symbol": self.symbol}

        return j_data


class Info(db.Model):
    """
    Class for describe Currency info ORM table.
    Use at Currensy table as personal info.
    
    """
    id = db.Column(db.Integer, primary_key=True)
    market_cap = db.Column(db.String(32))
    price = db.Column(db.String(32))
    cs = db.Column(db.String(32))
    volume = db.Column(db.String(32))
    perc_1h = db.Column(db.String(32))
    perc_7d = db.Column(db.String(32))
    perc_24h = db.Column(db.String(32))
    date = db.Column(db.DateTime)

    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency',
                               backref=db.backref('info', lazy='dynamic'))

    def __init__(self, mc, price, cs, volume,
                 p1h, p24h, p7d, datet, currency):
        self.market_cap = mc
        self.price = price
        self.cs = cs
        self.volume = volume
        self.perc_1h = p1h
        self.perc_24h = p24h
        self.perc_7d = p7d
        self.date = datet
        self.currency = currency

    def as_json(self):
        j_data = {"id": self.id,
                  "mc": self.market_cap,
                  "price": self.price,
                  "cs": self.cs,
                  "volume": self.volume,
                  "p1h": self.perc_1h,
                  "p24h": self.perc_24h,
                  "p7d": self.perc_7d,
                  "date": self.date}

        return j_data