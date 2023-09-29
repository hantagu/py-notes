import os
import hmac
import hashlib

from ssl import SSLContext, PROTOCOL_TLS_SERVER

import mysql.connector as mysql
from flask import Flask, Response, request, session, redirect, render_template, abort, url_for

from database import DBHelper


PAGE_ERROR = 'error'

PAGE_MAIN = 'main'
PAGE_BOOKS = 'books'

PAGE_LOGIN = 'login'
PAGE_LOGOUT = 'logout'


app = Flask(__name__)
app.secret_key = os.environ['APP_KEY']
bot_token = os.environ['BOT_TOKEN']
app.jinja_env.keep_trailing_newline = True


ctx = SSLContext(PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=f'./tls/{os.environ["LISTEN_ADDR"]}.crt', keyfile=f'./tls/{os.environ["LISTEN_ADDR"]}.key')


database = DBHelper(os.environ['MYSQL_HOST'], os.environ['MYSQL_USER'], os.environ['MYSQL_PASSWD'], os.environ['MYSQL_DATABASE'])


def error(msg: str) -> Response:
    return redirect(url_for('error_page', msg=msg))

@app.get('/error')
def error_page():
    return render_template(f'{PAGE_ERROR}.html', msg=request.args.get('msg', 'Неизвестная ошибка'))


@app.get('/')
def main_page():

    if not (user := database.auth(session)):
        session.clear()
        return render_template(f'{PAGE_MAIN}.html', page=PAGE_MAIN, user=None, notes_count=database.total_notes_count())

    return render_template(f'{PAGE_MAIN}.html', page=PAGE_MAIN, user=user)


@app.get(f'/{PAGE_LOGIN}')
def login_page():

    if not (tg_hash := request.args.get('hash')):
        return error('Параметр `hash` отсутствует в ответе от Telegram')

    sorted_args = [(k, v) for k, v in sorted(request.args.items(), key=lambda x: x[0]) if k != 'hash']

    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest() != tg_hash:
        return error('Нарушена целостность данных, полученных от Telegram')

    for k, v in sorted_args:
        session[k] = v

    return redirect(url_for('main_page'))


@app.get(f'/{PAGE_LOGOUT}')
def logout_page():
    session.clear()
    return redirect(url_for('main_page'))


@app.get(f'/{PAGE_BOOKS}')
def books_page():

    if not (user := database.auth(session)):
        return redirect(url_for('main_page'))

    books = database.get_books(user.id)

    return render_template(f'{PAGE_BOOKS}.html', page=PAGE_BOOKS, user=user, books=books)

@app.post(f'/{PAGE_BOOKS}')
def books_form():

    if not all((owner_id := session.get('id', None), title := request.form.get('title', None))):
        return error('Недостаточно аргументов')

    if not database.create_book(owner_id, title):
        return error('Ошибка обращения к БД')
    
    return redirect(url_for('books_page'))


app.run(os.environ["LISTEN_ADDR"], 443, ssl_context=ctx)