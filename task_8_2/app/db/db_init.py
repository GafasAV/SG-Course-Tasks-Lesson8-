from app.index import app
from app.db.models import db, User, Currency, Info
from app.scraper.scraper import Scraper

from datetime import datetime


__author__ = "Andrew Gafiychuk"


def add_some_user():

    user1 = User(username="User", email="user@mail.ru",
                 password="userpassword")
    user2 = User(username="Test", email="test@gmail.com",
                 password="password")
    user3 = User(username="Login", email="login@gmail.com",
                 password="loginpassword")

    return [user1, user2, user3]


def fill_currencys():
    sc = Scraper()
    data = sc.start()

    return data


if __name__ == '__main__':

    with app.app_context() as contex:
        db.init_app(contex.app)

        # Create DB's
        db.create_all()
        db.session.commit()

        # Add some users to user table...
        users = add_some_user()
        try:
            for user in users:
                db.session.add(user)

            db.session.commit()

        except Exception as err:
            print("Users data add Error...\n"
                  "{0}".format(err))

        # Add all virtual Currency to DB...
        data = fill_currencys()
        try:
            for rec in data:
                if not Currency.query.filter_by(name=rec[0].lower()).first():
                    currency = Currency(name=rec[0], symbol=rec[1])

                    db.session.add(currency)
                else:
                    continue

                db.session.commit()

        except Exception as err:
            print("Currency data add Error...\n"
                  "{0}".format(err))

        # Add Currency info to DB...
        data_t = datetime.now()
        count = 0
        try:
            for rec in data:
                currency = Currency.query.filter_by(
                    name=rec[0].lower()).first()

                if not currency:
                    continue

                info = Info(rec[2], rec[3], rec[4], rec[5],
                            rec[6], rec[7], rec[8], data_t,
                            currency=currency)

                currency.info.append(info)

                count += 1

            print("Done... ({0}) Write's !".format(count))

            db.session.commit()

        except Exception as err:
            print("Info data add Error...\n"
                  "{0}".format(err))
