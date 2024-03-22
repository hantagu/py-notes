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
from enums import HTTP, Page, Method, ErrorTexts


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
                return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidRequestFormat.value)
            return f(params)

        inner.__name__ = f.__name__
        return inner

    def wrapper_token(f: Callable[[dict[str, Any], dict[str, Any]], Response]) -> Callable[[], Response]:

        def inner() -> Response:

            try:
                params: dict[str, Any] = json.loads(request.get_data())
            except:
                return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidRequestFormat.value)

            try:
                raw_token: str = request.headers['X-Notes-Auth-Token']
            except:
                return APIError(HTTP.BadRequest.value, ErrorTexts.AuthenticationHeaderNotFound.value)

            try:
                token: dict[str, Any] = jwt.decode(raw_token, app.secret_key, algorithms=[jwt.get_unverified_header(raw_token)['alg']])
            except jwt.InvalidSignatureError:
                return APIError(HTTP.Unauthorized.value, ErrorTexts.InvalidTokenSignature.value)
            except jwt.ExpiredSignatureError:
                return APIError(HTTP.Unauthorized.value, ErrorTexts.TokenHasExpired.value)
            except jwt.DecodeError:
                return APIError(HTTP.Unauthorized.value, ErrorTexts.InvalidToken.value)

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
        return APIError(HTTP.InternalServerError.value, ErrorTexts.FailedToGetStatistics.value)


@app.post(f'/method/{Method.Login.value}')
@APIRequest(False) # type: ignore
def login(params: dict[str, Any]) -> Response:
    try:
        hash: str = params['hash']
        id: int = int(params['id'])
        first_name: str = params['first_name']
        auth_date: int = int(params['auth_date'])
    except ValueError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidArgumentValue.value)
    except KeyError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.NotEnoughArguments.value)

    sorted_args = [(k, v) for k, v in sorted(params.items(), key=lambda x: x[0]) if k != 'hash']
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_args])
    secret_key = sha256(bot_token.encode()).digest()

    if hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest() != hash:
        return APIError(HTTP.BadRequest.value, ErrorTexts.DataIsNotFromTelegram.value)

    timestamp = int(time())
    if timestamp - auth_date > 300:
        return APIError(HTTP.BadRequest.value, ErrorTexts.DataIsOutdated.value)

    try:
        database.create_user(id, params.get('username', None), first_name, params.get('last_name', None))
    except psycopg.errors.UniqueViolation:
        pass

    auth_token = jwt.encode({'sub': id, 'iat': timestamp, 'exp': timestamp+86400}, app.secret_key)
    return APIResult({'auth_token': auth_token})


@app.post(f'/method/{Method.GetMe.value}')
@APIRequest(True) # type: ignore
def get_me(token: dict[str, Any], _: dict[str, Any]) -> Response:
    try:
        user: User | None = database.get_user(token['sub'])
        if user:
            return APIResult({'user': user.to_json()})
        else:
            return APIError(HTTP.NotFound.value, ErrorTexts.UserNotFound.value)
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)


@app.post(f'/method/{Method.GetBooks.value}')
@APIRequest(True) # type: ignore
def get_books(token: dict[str, Any], _: dict[str, Any]) -> Response:
    try:
        books: list[tuple[Book, int]] = database.get_books(token['sub'])
        return APIResult({'entries': [(book.to_json(), amount) for book, amount in books]})
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)



@app.post(f'/method/{Method.CreateBook.value}')
@APIRequest(True) # type: ignore
def create_book(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        title: str = str(params['title'])
        if not 1 <= len(title) <= 64:
            raise ValueError
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')

    try:
        book: Book = database.create_book(int(token['sub']), title)
        return APIResult({'book': book.to_json()})
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')


@app.post(f'/method/{Method.DeleteBook.value}')
@APIRequest(True) # type: ignore
def delete_book(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        id: UUID = UUID(params['id'])
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')

    try:
        book: Book | None = database.delete_book(token['sub'], id)
        if book:
            return APIResult({'book': book.to_json()})
        else:
            return APIError(HTTP.NotFound.value, 'book not found')
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')



@app.post(f'/method/{Method.GetNotes.value}')
@APIRequest(True) # type: ignore
def get_notes(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        book_id: UUID = UUID(params['book_id'])
    except ValueError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidArgumentValue.value)
    except KeyError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.NotEnoughArguments.value)

    try:
        notes: list[Note] = database.get_notes(token['sub'], book_id)
        return APIResult({'notes': [note.to_json() for note in notes]})
    except NotExistsException:
        return APIError(HTTP.NotFound.value, ErrorTexts.BookNotFound.value)
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)


@app.post(f'/method/{Method.CreateNote.value}')
@APIRequest(True) # type: ignore
def create_note(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        book_id: UUID = UUID(params['book_id'])
        title: str = str(params['title'])
        text: str = str(params['text'])
        if not all((1 <= len(title) <= 64, 1 <= len(text) <= 4096)):
            raise ValueError
    except ValueError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidArgumentValue.value)
    except KeyError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.NotEnoughArguments.value)

    try:
        note: Note = database.create_note(token['sub'], book_id, title, text)
        return APIResult({'note': note.to_json()})
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)


@app.post(f'/method/{Method.DeleteNote.value}')
@APIRequest(True) # type: ignore
def delete_note(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        book_id: UUID = UUID(params['book_id'])
        id: UUID = UUID(params['id'])
    except ValueError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidArgumentValue.value)
    except KeyError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.NotEnoughArguments.value)

    try:
        note: Note | None = database.delete_note(token['sub'], book_id, id)
        if note:
            return APIResult({'note': note.to_json()})
        else:
            return APIError(HTTP.NotFound.value, ErrorTexts.NoteNotFound.value)
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)


@app.post(f'/method/{Method.GetTaskLists.value}')
@APIRequest(True) # type: ignore
def get_task_lists(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        task_lists: list[tuple[TaskList, list[Task]]] = database.get_task_lists(token['sub'])
        return APIResult({'entries': [{'task_list': task_list.to_json(), 'tasks': [task.to_json() for task in tasks]} for task_list, tasks in task_lists]})
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)


@app.post(f'/method/{Method.CreateTaskList.value}')
@APIRequest(True) # type: ignore
def create_task_list(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        title: str = str(params['title'])
        tasks: list[str] = params['tasks']
        if not 1 <= len(title) <= 64 or not all((1 <= len(i) <= 64) for i in tasks):
            raise ValueError
    except ValueError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.InvalidArgumentValue.value)
    except KeyError:
        return APIError(HTTP.BadRequest.value, ErrorTexts.NotEnoughArguments.value)

    try:
        task_list: tuple[TaskList, list[Task]] = database.create_task_list(token['sub'], title, tasks)
        return APIResult({'task_list': task_list[0].to_json(), 'tasks': [i.to_json() for i in task_list[1]]})
    except:
        return APIError(HTTP.InternalServerError.value, ErrorTexts.InternalServerError.value)


@app.post(f'/method/{Method.DeleteTaskList.value}')
@APIRequest(True) # type: ignore
def delete_task_list(token: dict[str, Any], params: dict[str, Any]) -> Response:
    try:
        id: UUID = UUID(params['id'])
    except ValueError:
        return APIError(HTTP.BadRequest.value, 'invalid argument value')
    except KeyError:
        return APIError(HTTP.BadRequest.value, 'not enough arguments')

    try:
        task_list: TaskList | None = database.delete_task_list(token['sub'], id)
        if task_list:
            return APIResult({'task_list': task_list.to_json()})
        else:
            return APIError(HTTP.NotFound.value, 'task_list not found')
    except:
        return APIError(HTTP.InternalServerError.value, 'internal server error')


app.run(os.environ['LISTEN_ADDR'], int(os.environ['LISTEN_PORT']), ssl_context=ctx, debug=True)
