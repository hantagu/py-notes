import os
from time import time
import json

from hashlib import sha256
import hmac
from ssl import SSLContext, PROTOCOL_TLS_SERVER

from collections import OrderedDict
from collections.abc import Callable
from typing import Any
from uuid import UUID

import dotenv
import jwt
import psycopg
from flask import Flask, Response, make_response, render_template, request

from database import DBHelper, User, Book, Note, TaskList, Task, NotExistsException
from enums import HTTP, Page, Method


dotenv.load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.environ['APP_KEY']
bot_token = os.environ['BOT_TOKEN']
app.jinja_env.auto_reload = True


ctx = SSLContext(PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=os.environ['TLS_CERT'], keyfile=os.environ['TLS_KEY'])


database = DBHelper(os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT']), os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWD'], os.environ['POSTGRES_DBNAME'])



def APIRequest(check_token: bool) -> Callable[[Callable[[dict[str, Any]], Response]], Callable[[], Response]] | Callable[[Callable[[dict[str, Any], dict[str, Any]], Response]], Callable[[], Response]]:

    def wrapper(f: Callable[[dict[str, Any]], Response]) -> Callable[[], Response]:

        def inner() -> Response:
            try:
                params: dict[str, Any] = json.loads(request.get_data())
            except:
                return APIError(HTTP.BadRequest.value, 'invalid request format')
            return f(params)

        inner.__name__ = f.__name__
        return inner

    def wrapper_token(f: Callable[[dict[str, Any], dict[str, Any]], Response]) -> Callable[[], Response]:

        def inner() -> Response:

            try:
                params: dict[str, Any] = json.loads(request.get_data())
            except:
                return APIError(HTTP.BadRequest.value, 'invalid request format')

            try:
                raw_token: str = request.headers['X-Notes-Auth-Token']
            except:
                return APIError(HTTP.BadRequest.value, 'X-Notes-Auth-Token header not found')

            try:
                token: dict[str, Any] = jwt.decode(raw_token, app.secret_key, algorithms=[jwt.get_unverified_header(raw_token)['alg']])
            except jwt.InvalidSignatureError:
                return APIError(HTTP.Unauthorized.value, 'invalid token signature')
            except jwt.ExpiredSignatureError:
                return APIError(HTTP.Unauthorized.value, 'token has expired')

            return f(token, params)

        inner.__name__ = f.__name__
        return inner

    return wrapper_token if check_token else wrapper


def APIResult(result: dict[str, Any]) -> Response:
    r = make_response(json.dumps(OrderedDict([('ok', True), ('result', result)])))
    r.content_type = 'application/json'
    return r


def APIError(http_code: int, description: str) -> Response:
    r = make_response(json.dumps(OrderedDict([('ok', False), ('description', description)])), http_code)
    r.content_type = 'application/json'
    return r



@app.get('/')
def main() -> Response:
    return make_response(render_template(f'{Page.Main.value}.html'))


@app.get(f'/{Page.Books.value}')
def books() -> Response:
    return make_response(render_template(f'{Page.Books.value}.html'))


@app.get(f'/{Page.Notes.value}')
def notes() -> Response:
    return make_response(render_template(f'{Page.Notes.value}.html'))


@app.get(f'/{Page.TaskLists.value}')
def task_lists() -> Response:
    return make_response(render_template(f'{Page.TaskLists.value}.html'))



@app.post(f'/method/{Method.GetStatistics.value}')
@APIRequest(False) # type: ignore
def get_statistics(_: dict[str, Any]):
    try:
        return APIResult({'statistics': {'notes': database.total_notes_amount(), 'task_lists': database.total_task_lists_amount()}})
    except:
        return APIError(HTTP.InternalServerError.value, 'failed to get statistics')


@app.post(f'/method/{Method.Login.value}')
@APIRequest(False) # type: ignore
def login(params: dict[str, Any]) -> Response:
    try:
        hash: str = params['hash']
        id: int = int(params['id'])
        first_name: str = params['first_name']
        auth_date: int = int(params['auth_date'])
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')

    sorted_args = [(k, v) for k, v in sorted(params.items(), key=lambda x: x[0]) if k != 'hash']
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest() != hash:
        return APIError(HTTP.BadRequest.value, 'data is not from Telegram')

    timestamp = int(time())
    if timestamp - auth_date > 300:
        return APIError(HTTP.BadRequest.value, 'data is outdated')

    try:
        database.create_user(id, params.get('username', None), first_name, params.get('last_name', None))
    except psycopg.errors.UniqueViolation:
        pass

    auth_token = jwt.encode({'iss': 'https://91.215.155.252:443/', 'sub': id, 'iat': timestamp, 'exp': timestamp+86400}, app.secret_key)
    return APIResult({'auth_token': auth_token})


@app.post(f'/method/{Method.GetMe.value}')
@APIRequest(True) # type: ignore
def get_me(token: dict[str, Any], _: dict[str, Any]) -> Response:
    try:
        user: User | None = database.get_user(token['sub'])
        if user:
            return APIResult({'user': {'id': user.id, 'username': user.username, 'first_name': user.first_name, 'last_name': user.last_name}})
        else:
            return APIError(HTTP.NotFound.value, 'user not found')
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')


@app.post(f'/method/{Method.GetBooks.value}')
@APIRequest(True) # type: ignore
def get_books(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        books = database.get_books(token['sub'])
        return APIResult({'books': [{'id': str(book.id), 'owner_id': book.owner_id, 'title': book.title, 'notes_amount': amount} for book, amount in books]})
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')



@app.post(f'/method/{Method.CreateBook.value}')
@APIRequest(True) # type: ignore
def create_book(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        title: str = str(params['title'])
        if not 1 <= len(title) <= 64:
            raise ValueError
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')

    try:
        book: Book = database.create_book(int(token['sub']), title)
        return APIResult({'book': {'id': str(book.id), 'owner_id': book.owner_id, 'title': book.title}})
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')


@app.post(f'/method/{Method.DeleteBook.value}')
@APIRequest(True) # type: ignore
def delete_book(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        id: UUID = UUID(params['id'])
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')

    try:
        book: Book | None = database.delete_book(token['sub'], id)
        if book:
            return APIResult({'book': {'id': str(book.id), 'owner_id': book.owner_id, 'title': book.title}})
        else:
            return APIError(HTTP.NotFound.value, 'book not found')
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')



@app.post(f'/method/{Method.GetNotes.value}')
@APIRequest(True) # type: ignore
def get_notes(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        book_id: UUID = UUID(params['book_id'])
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')

    try:
        notes: list[Note] = database.get_notes(token['sub'], book_id)
        return APIResult({'notes': [{'id': str(note.id), 'book_id': str(note.book_id), 'title': note.title, 'text': note.text} for note in notes]})
    except NotExistsException:
        return APIError(HTTP.NotFound.value, 'book not found')
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')


@app.post(f'/method/{Method.CreateNote.value}')
@APIRequest(True) # type: ignore
def create_note(token: dict[str, Any], params: dict[str, Any]) -> Response:
    return APIError(HTTP.NotImplemented.value, 'not implemented yet')


@app.post(f'/method/{Method.DeleteNote.value}')
@APIRequest(True) # type: ignore
def delete_note(token: dict[str, Any], params: dict[str, Any]) -> Response:
    return APIError(HTTP.NotImplemented.value, 'not implemented yet')


@app.post(f'/method/{Method.GetTaskLists.value}')
@APIRequest(True) # type: ignore
def get_task_lists(token: dict[str, Any], params: dict[str, Any]) -> Response:
    return APIError(HTTP.NotImplemented.value, 'not implemented yet')


@app.post(f'/method/{Method.CreateTaskList.value}')
@APIRequest(True) # type: ignore
def create_task_list(token: dict[str, Any], params: dict[str, Any]) -> Response:
    return APIError(HTTP.NotImplemented.value, 'not implemented yet')


@app.post(f'/method/{Method.DeleteTaskList.value}')
@APIRequest(True) # type: ignore
def delete_task_list(token: dict[str, Any], params: dict[str, Any]) -> Response:
    return APIError(HTTP.NotImplemented.value, 'not implemented yet')


app.run(os.environ['LISTEN_ADDR'], int(os.environ['LISTEN_PORT']), ssl_context=ctx)
