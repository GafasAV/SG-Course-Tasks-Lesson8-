import schedule
import logging

from os import urandom
from time import sleep
from functools import wraps
from datetime import datetime
from threading import Thread

from flask import Flask, flash, redirect, render_template, \
    url_for, session, g, jsonify, request
from flask_bootstrap import Bootstrap

from app.forms import LoginForm, RegisterForm, UserControlForm
from app.db.models import db, User, Currency, Info
from app.scraper.scraper import Scraper

from werkzeug.security import check_password_hash


app = Flask(__name__)

app.config['SECRET_KEY'] = urandom(64)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BG_TASK_TIME'] = 10

Bootstrap(app)
db.init_app(app)


@app.before_request
def before_request():
    """
    Check global user before eache requests.
    
    """
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.before_first_request
def initialize():
    """
    Initializing BG Task for Data Scrapping.
    Time delta in app.config[BG_TASK_TIME]
    
    """
    logging.debug("[+]Initializing app BG Task...")

    time_delta = app.config['BG_TASK_TIME']

    schedule.every(time_delta).minutes.do(background_task)

    bg_task = Thread(target=run)
    bg_task.start()


def check_login(f):
    """
    Check user login session is exists.
    User one session for eache users.
     
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('index'))
        elif g.user == kwargs['user']:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('info', user=g.user))

    return decorated_function


def is_login(f):
    """
    Redirect logined user from Reg and Log form to home page.
    
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user:
            return redirect(url_for('info', user=g.user))

        return f(*args, **kwargs)

    return wrapper


def check_api_key(f):
    """
    Check valid API_KEY for REST API.
     
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        users = User.query.all()

        for user in users:
            if kwargs['api_key'] == user.apiid:
                return f(*args, **kwargs)

        return jsonify({'ERROR': 'API Key Error !!!'})

    return wrapper


@app.route('/')
@app.route('/index/', methods=['GET', 'POST'])
def index():
    """
    Main page function.
    
    """
    if g.user:
        user = session['user']
        api_id = session['api_id']

    else:
        user = None
        api_id = None

    return render_template('index.html',
                           user=user, api=api_id)


@app.route('/login/', methods=['GET', 'POST'])
@is_login
def login():
    """
    Login form function.
    
    """
    log_form = LoginForm()

    if log_form.validate_on_submit():
        t_username = log_form.username.data
        t_password = log_form.password.data

        try:
            user = User.query.filter_by(
                user_name=t_username.lower()).first()

            if user:
                if check_password_hash(user.password, t_password):
                    session['user'] = user.user_name
                    session['api_id'] = user.apiid

                    return redirect(url_for(
                        'info', user=session['user'], api=session['api_id']))
                else:
                    flash('Invalid username or password !')
            else:
                flash('This username not in system !')

        except Exception as err:
            return '<h3>Some error...</h3>{0}'\
                .format(err)

    return render_template('login.html', form=log_form)


@app.route('/register/', methods=['GET', 'POST'])
@is_login
def register():
    """
    Register form function.
    
    """
    reg_form = RegisterForm()

    if reg_form.validate_on_submit():
        t_username = reg_form.username.data
        t_password = reg_form.password.data
        t_email = reg_form.email.data

        user = User.query.filter_by(
            user_name=t_username.lower()).first()
        if user:
            flash('This Username already exist... Try other!')

            return redirect(url_for('register'))

        new_user = User(username=t_username,
                        email=t_email, password=t_password)

        try:
            db.session.add(new_user)
            db.session.commit()

            flash('Success ! Try Login...')

            return redirect(url_for('login'))

        except Exception as err:
            db.session.rollback()

            return '<h3>Some error...</h3>{0}'\
                .format(err)

    return render_template('register.html', form=reg_form)


@app.route('/info/<user>/', methods=['GET', 'POST'])
@check_login
def info(user):
    """
    User Info page function.
    
    """
    uform = UserControlForm()
    api = session['api_id']

    # User Get Currency data.
    if uform.currencys.data:
        db_query = Currency.query.all()

        if not db_query:
            flash('Data Error...')

        data = []

        for obj in db_query:
            data.append((obj.name.capitalize(), obj.symbol,))

        return render_template('info/currencys.html', user=user,
                               data=data, api=api, uform=uform)

    # User Get Online data.
    elif uform.online.data:
        sc = Scraper()
        data = sc.start()

        try:
            date_t = datetime.now()

            for rec in data:
                currency = Currency.query.filter_by(
                    name=rec[0].lower()).first()

                if not currency:
                    continue

                info = Info(rec[2], rec[3], rec[4], rec[5],
                            rec[6], rec[7], rec[8], date_t, currency=currency)

                currency.info.append(info)
                db.session.commit()

            return render_template('info/online.html', user=user,
                                   data=data, api=api, uform=uform,
                                   online=True)

        except Exception as err:
            db.session.rollback()

            return '<h3>Some error...</h3>{0}'\
                .format(err)

    # User Get data from DB.
    elif uform.get_history.data:
        currency = uform.curr_name.data
        if not currency:
            flash("Input Currency name or Symbol to search!")

        if currency.isupper():
            curr_query = Currency.query.filter_by(symbol=currency).first()
        else:
            curr_query = Currency.query.filter_by(
                name=currency.lower()).first()

        if not curr_query:
            flash('No such currensy: In Name or Symbol'.format(currency))

            return render_template('info.html', user=user,
                                   data=None, api=api, uform=uform)

        data = []

        history = curr_query.info.all()
        for obj in history:
            data.append((obj.market_cap, obj.price, obj.cs,
                         obj.volume, obj.perc_1h, obj.perc_24h,
                         obj.perc_7d, obj.date,))

        return render_template('info/history.html', user=user,
                               currency=currency, data=data, api=api,
                               uform=uform)

    return render_template('info.html', user=user,
                           data=None, api=api, uform=uform)


@app.route('/user_logout/<user>')
def user_logout(user):
    """
    User Logout.
    Delete user session.
     
    """
    if g.user == user:
        session.pop('user', None)
        session.clear()

    return redirect(url_for('index'))


@app.errorhandler(404)
def err404(e):
    """
    Error 404 page.
     
    """
    return render_template('err_pages/err404.html', error=e)


@app.route('/api/<api_key>/currency/', methods=['GET'])
@check_api_key
def get_all(api_key):
    """
    REST API to GET all Currency in DB.
     
    """
    curr_query = Currency.query.all()
    if not curr_query:
        return jsonify({'ERROR': 'No such data !'})

    data = []
    for obj in curr_query:
        data.append({'name': obj.name, 'sym': obj.symbol})

    return jsonify({'data': data})


@app.route('/api/<api_key>/currency/<name>/', methods=['GET'])
@check_api_key
def get_one(api_key, name):
    """
    REST API to GET Currency Info by name or symbol.
     
    """
    if name.isupper():
        curr_query = Currency.query.filter_by(symbol=name).first()
    else:
        curr_query = Currency.query.filter_by(name=name.lower()).first()

    if not curr_query:
        return jsonify({'ERROR': 'No data by: {0}'.format(name)})

    his_query = curr_query.info.all()
    if not his_query:
        return jsonify({'name': curr_query.name, 'symb': curr_query.symbol,
                 'history': 'No Quotation history now...'})

    history = []
    for obj in his_query:
        history.append({'market cap': obj.market_cap, 'price': obj.price,
                        'cs': obj.cs, 'volume': obj.volume,
                        '%1h': obj.perc_1h, '%24h': obj.perc_24h,
                        '%7d': obj.perc_7d, 'date-time': obj.date})

    return jsonify({'name': curr_query.name, 'symb': curr_query.symbol,
                    'history': history})


@app.route('/api/<api_key>/currency/', methods=['POST'])
@check_api_key
def post_one(api_key):
    """
    REST API to POST data in DB.
    Params: name, symbol,
            info: {ms, price, cs, volume, p1h, p24h, p7d, data_time}
     
    """
    data = request.data

    if not data:
        return jsonify({'ERROR': 'No data to ADD!',
                        "Template:": "name: Bitcoin, symbol: BTC, info: {}",
                        "Info params:": "ms, price, cs, volume, p1h, p24h, p7d, date_time",
                        "Data Format": "JSON"})

    data = request.get_json()

    if not data['name'] or not data['symbol']:
        return jsonify({'ERROR': 'No some data field!',
                        "Template:": "name: Bitcoin, symbol: BTC, info: {}",
                        "Info params:": "ms, price, cs, volume, p1h, p24h, p7d, date_time",
                        "Data Format": "JSON"})

    curr_query = Currency.query.filter_by(name=data['name'].lower()).first()

    if 'info' not in data.keys():
        info = None
    else:
        d_info = data['info']
        date_time = datetime.strptime(d_info['date_time'], "%Y-%m-%d %H:%M:%S")

        info = Info(mc=d_info['mc'], price=d_info['price'], cs=d_info['cs'],
                    volume=d_info['volume'], p1h=d_info['p1h'],
                    p24h=d_info['p24h'], p7d=d_info['p7d'],
                    datet=date_time, currency=None)

    if curr_query and not info:
        return jsonify({'ERROR': 'This currency alredy exists',
                        "Template:": "name: Bitcoin, symbol: BTC, info: {}",
                        "Info params:": "ms, price, cs, volume, p1h, p24h, p7d, date_time",
                        "Data Format": "JSON"})
    elif curr_query and info:
        try:
            curr_query.info.append(info)
            db.session.commit()

            return jsonify({"Status": "Success! Info Add..."})

        except Exception as err:
            db.session.rollback()

            print("[+]REST API Add Currency Info Error...\n"
                  "{0}".format(err))

            return jsonify({'ERROR': 'Data Add some error! Try later!'})

    try:
        new_curr = Currency(name=data['name'], symbol=data['symbol'])
        if info:
            new_curr.info = info

        db.session.add(new_curr)
        db.session.commit()

        return jsonify({"Status": "Success!"})

    except Exception as err:
        db.session.rollback()

        print("[+]REST API Add Currency Error...\n"
              "{0}".format(err))

        return jsonify({'ERROR': 'Data Add some error! Try later!'})


@app.route('/api/<api_key>/currency/', methods=['DELETE'])
@check_api_key
def del_one(api_key):
    """
    REST API to DELETE data from DB.
    Params: name.
    
    """
    data = request.data
    if not data:
        return jsonify({'ERROR': 'No params to DEL data',
                        "Template:": "name: Bitcoin",
                        "Data Format": "JSON"})

    data = request.get_json()

    if 'name' not in data.keys():
        return jsonify({'ERROR': 'To DEL data set <name> param!',
                        "Template:": "name: Bitcoin",
                        "Data Format": "JSON"})

    currency = data['name']
    curr_query = Currency.query.filter_by(name=currency.lower()).first()
    if not curr_query:
        return jsonify({"ERROR:": "Data DEL error."
                                  "Currency with name {0} not exist!"
                       .format(currency)})

    history_query = curr_query.info.all()
    try:
        if history_query:
            for record in history_query:
                db.session.delete(record)

        db.session.delete(curr_query)
        db.session.commit()

        return jsonify({"Status:": "Success !"})

    except Exception as err:
        db.session.rollback()

        print("[+]REST API DEL Data error...\n"
              "{0}".format(err))

        return jsonify({'ERROR': 'Data DEL some error! Try later!'})


def background_task():
    sc = Scraper()
    data = sc.start()

    with app.app_context():

        try:
            date_t = datetime.now()

            for rec in data:
                currency = Currency.query.filter_by(
                    name=rec[0].lower()).first()

                if not currency:
                    continue

                info = Info(rec[2], rec[3], rec[4], rec[5],
                            rec[6], rec[7], rec[8], date_t, currency=currency)

                currency.info.append(info)
                db.session.commit()

            print("[Background:] New data added to DB.")

        except Exception as err:
            db.session.rollback()

            print('Background task Error...\n'
                  '{0}'.format(err))


def run():
    logging.debug("[+]BG Task Running...")

    while 1:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("[+]Flask App Started...")

    app.debug = True
    app.run()
