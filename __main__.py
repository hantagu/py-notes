import os
from time import time, sleep
import json

from uuid import UUID
from hashlib import sha256
import hmac
from ssl import SSLContext, PROTOCOL_TLS_SERVER

from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import jwt
from dotenv import load_dotenv
import psycopg
from flask import Flask, Response, jsonify, make_response, redirect, render_template, url_for, request, session

from database import DBHelper, User


HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404

HTTP_INTERNAL_SERVER_ERROR = 500


PAGE_MAIN = 'main'

PAGE_BOOKS = 'books'
METHOD_CREATE_BOOK = 'method/create_book'
METHOD_DELETE_BOOK = 'method/delete_book'

PAGE_NOTES = 'notes'
METHOD_CREATE_NOTE = 'method/create_note'
METHOD_DELETE_NOTE = 'method/delete_note'

PAGE_TASK_LISTS = 'task_lists'
METHOD_CREATE_TASK_LIST = 'method/create_task_list'
METHOD_DELETE_TASK_LIST = 'method/delete_task_list'

METHOD_LOGIN = 'method/login'
METHOD_GET_ME = 'method/get_me'
METHOD_GET_STATISTICS = 'method/get_statistics'


load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.environ['APP_KEY']
bot_token = os.environ['BOT_TOKEN']
app.jinja_env.auto_reload = True


ctx = SSLContext(PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=os.environ['TLS_CERT'], keyfile=os.environ['TLS_KEY'])


database = DBHelper(os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT']), os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWD'], os.environ['POSTGRES_DBNAME'])


@app.get('/')
def main() -> Response:
    return make_response(render_template(f'{PAGE_MAIN}.html'))


@app.get(f'/{PAGE_BOOKS}')
def books() -> Response:
    return make_response(render_template(f'{PAGE_BOOKS}.html'))


@app.get(f'/{PAGE_NOTES}')
def notes() -> Response:
    return make_response(render_template(f'{PAGE_NOTES}.html'))


@app.get(f'/{PAGE_TASK_LISTS}')
def task_lists() -> Response:
    return make_response(render_template(f'{PAGE_TASK_LISTS}.html'))



def APIRequest(check_token: bool) -> Callable[[Callable[[dict[str, Any]], Response]], Callable[[], Response]] | Callable[[Callable[[dict[str, Any], dict[str, Any]], Response]], Callable[[], Response]]:

    def wrapper(f: Callable[[dict[str, Any]], Response]) -> Callable[[], Response]:

        def inner() -> Response:
            try:
                params: dict[str, Any] = json.loads(request.get_data())
            except:
                return APIError(HTTP_BAD_REQUEST, 'invalid request format')
            return f(params)

        inner.__name__ = f.__name__
        return inner

    def wrapper_token(f: Callable[[dict[str, Any], dict[str, Any]], Response]) -> Callable[[], Response]:

        def inner() -> Response:

            try:
                params: dict[str, Any] = json.loads(request.get_data())
            except:
                return APIError(HTTP_BAD_REQUEST, 'invalid request format')

            try:
                raw_token: str = request.headers['X-Notes-Auth-Token']
            except:
                return APIError(HTTP_BAD_REQUEST, 'token not found')

            try:
                token: dict[str, Any] = jwt.decode(raw_token, app.secret_key, algorithms=[jwt.get_unverified_header(raw_token)['alg']])
            except jwt.InvalidSignatureError:
                return APIError(HTTP_UNAUTHORIZED, 'invalid token signature')
            except jwt.ExpiredSignatureError:
                return APIError(HTTP_UNAUTHORIZED, 'token has expired')

            return f(token, params)

        inner.__name__ = f.__name__
        return inner

    return wrapper_token if check_token else wrapper



def APIError(http_code: int, description: str) -> Response:
    r = make_response(json.dumps(OrderedDict([('ok', False), ('description', description)])), http_code)
    r.content_type = 'application/json'
    return r


def APIResult(*result) -> Response:
    r = make_response(json.dumps(OrderedDict([('ok', True), ('result', OrderedDict(result))])))
    r.content_type = 'application/json'
    return r



@app.post(f'/{METHOD_LOGIN}')
@APIRequest(False) # type: ignore
def login(params: dict[str, Any]) -> Response:

    try:
        hash = params['hash']
        id = int(params['id'])
        first_name = params['first_name']
        auth_date = int(params['auth_date'])
    except KeyError:
        return APIError(HTTP_BAD_REQUEST, 'not enough arguments')

    sorted_args = [(k, v) for k, v in sorted(params.items(), key=lambda x: x[0]) if k != 'hash']
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest() != hash:
        return APIError(HTTP_BAD_REQUEST, 'data is not from Telegram')

    timestamp = int(time())
    if timestamp - auth_date > 300:
        return APIError(HTTP_BAD_REQUEST, 'data is outdated')

    database.create_user(id, params.get('username', None), first_name, params.get('last_name', None))

    auth_token = jwt.encode({'iss': 'https://91.215.155.252:443/', 'sub': id, 'iat': timestamp, 'exp': timestamp+86400}, app.secret_key)
    return APIResult(('auth_token', auth_token))


@app.post(f'/{METHOD_GET_ME}')
@APIRequest(True) # type: ignore
def get_me(token: dict[str, Any], _: dict[str, Any]) -> Response:
    if (user := database.get_user(token['sub'])):
        return APIResult(('id', user.id), ('username', user.username), ('first_name', user.first_name), ('last_name', user.last_name))
    else:
        return APIError(HTTP_NOT_FOUND, 'user not found')


@app.post(f'/{METHOD_GET_STATISTICS}')
@APIRequest(False) # type: ignore
def get_statistics(_: dict[str, Any]):
    return APIResult(('notes', -3), ('task_lists', 0.4))


# @app.post(f'/{METHOD_CREATE_BOOK}')
# @auth_splitted
# def create_book() -> tuple[Callable[[User], Response], Callable[[], Response]]:

#     def ok(user: User) -> Response:
#         if not (title := request.form.get('title', None)):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.create_book(user.id, title):
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(books.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_DELETE_BOOK}')
# @auth_splitted
# def delete_book():

#     def ok(user: User) -> Response:
#         if not (book_id := request.form.get('book_id')):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.delete_book(user.id, UUID(book_id)):
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(books.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_CREATE_NOTE}')
# @auth_splitted
# def create_note():

#     def ok(user: User) -> Response:
#         if not all((book_id := request.form['book_id'], title := request.form['title'], text := request.form['text'])):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.create_note(user.id, UUID(book_id), title, text):
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(notes.__name__, book_id=book_id)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_DELETE_NOTE}')
# @auth_splitted
# def delete_note():

#     def ok(user: User) -> Response:
#         return redirect(url_for(main.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


# @app.post(f'/{METHOD_CREATE_TASK_LIST}')
# @auth_splitted
# def create_task_list():

#     def ok(user: User) -> Response:
#         if not all((title := request.form.get('title', None), tasks := request.form.getlist('task'))):
#             return redirect(url_for(error.__name__, msg='Недостаточно аргументов')) # type: ignore
#         if not database.create_tasklist(user.id, title, tasks): # type: ignore
#             return redirect(url_for(error.__name__, msg='Ошибка обращения к БД')) # type: ignore
#         return redirect(url_for(task_lists.__name__)) # type: ignore

#     def err() -> Response:
#         return redirect(url_for(error.__name__, msg='Ошибка аутентификации')) # type: ignore

#     return ok, err


app.run(os.environ['LISTEN_ADDR'], int(os.environ['LISTEN_PORT']), ssl_context=ctx)
