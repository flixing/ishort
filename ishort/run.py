import os
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, render_template, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug import check_password_hash, generate_password_hash, secure_filename
from flask_mail import Mail, Message

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

"""CONFIGURATIONS OF APP"""
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI ='sqlite:///' + os.path.join(basedir, 'data.sqlite'),
    SECRET_KEY='not a password',
    DEBUG=True,
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True,
    PER_PAGE=10,
    ))

app.config['MAIL_SERVER'] = ''
app.config['MAIL_PORT'] = ''
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, index=True)
    status = db.Column(db.Integer)

    def __init__(self, name, email, senha_hash, date=None, status=None):
        self.name = name
        self.email = email
        self.senha_hash = senha_hash
        if date is None:
            self.date = datetime.now()
        if status is None:
            self.status = False


class Url(db.Model):
    __tablename__ = 'url'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.Integer)

    def __init__(self, url, user, status=None, date=None):
        self.url = url
        self.user= user
        if date is None:
            self.date = datetime.now()
        if status is None:
            self.status = True


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        url = Url(url=request.form['link'], user=session['id'])
        db.session.add(url)
        db.session.commit()
    return render_template('home.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if session.get('logged_in'):
        return redirect(url_for('home'))
    if request.method == 'POST':
        user = User(name=request.form['name'],
                            email=request.form['email'],
                            senha_hash=request.form['password'])

        db.session.add(user)
        db.session.commit()
        flash('Cadastrado com sucesso.')
        return redirect(url_for('home'))
    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """login of users"""
    """TODO VERIFICAR O STATUS DA CONTA, SE Ja FOI ATIVADA PARA PERMITIR O LOGIN"""
    if session.get('logged_in'):
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        row = None
        row = User.query.filter_by(email=request.form['email'],
                                           senha_hash=request.form['password']).first()
        if row is None:
            flash('username is invalid')
            return render_template('login.html', error=error)
        elif not row.status:
            flash('Favor verificar seu email')
            error = 'favor verificar seu email'
            return render_template('login.html', error=error)
        else:
            session['logged_in'] = True
            session['name'] = row.name
            session['email'] = row.email
            session['senha_hash'] = row.senha_hash
            session['status'] = row.status
            session['id'] = row.id
            flash('You were logged in')
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    """logout of user"""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('home'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    tab = request.args.get('tab')
    if tab == 'data':
        if request.method == 'POST':
            user = User.query.get(session['id'])
            user.name = request.form['name']
            session['name'] = request.form['name']
            user.email = request.form['email']
            session['email'] = request.form['email']
            db.session.commit()
            return render_template('settings.html', tab=tab)
    elif tab == 'password':
        if request.method == 'POST' and (request.form['password'] == request.form['password2']) and (request.form['password_old'] == session['senha_hash']):
            user = User.query.get(session['id'])
            user.senha_hash = request.form['password']
            session['senha_hash'] = request.form['password']
            db.session.commit()
            return render_template('settings.html', tab=tab)
    elif tab == 'account':
        if request.method == 'POST' and (request.form['password'] == session['senha_hash']):
            user = User.query.get(session['id'])
            user.status = False
            db.session.commit()
            flash('Sua conta foi desativada')
            return redirect(url_for('logout'))
    return render_template('settings.html', tab=tab)


if __name__ == '__main__':
    app.run(debug=True)
