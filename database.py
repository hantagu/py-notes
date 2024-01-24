import sys
from uuid import UUID, uuid4
from datetime import datetime

import psycopg


class User:

    def __init__(self, id: int, username: str | None, first_name: str, last_name: str | None) -> None:
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}' if self.last_name else self.first_name


class Book:

    def __init__(self, id: UUID, owner_id: UUID, title: str) -> None:
        self.id = id
        self.owner_id = owner_id
        self.title = title


class Note:

    def __init__(self, id: UUID, book_id: UUID, title: str, text: str) -> None:
        self.id = id
        self.book_id = book_id
        self.title = title
        self.text = text


class TaskList:

    def __init__(self, id: UUID, owner_id: UUID, title: str) -> None:
        self.id = id
        self.owner_id = owner_id
        self.title = title


class Task:

    def __init__(self, id: UUID, tasklist_id: UUID, title: str, is_done: bool) -> None:
        self.id = id
        self.tasklist_id = tasklist_id
        self.title = title
        self.is_done = is_done


class DBHelper:

    __TABLE_USERS = 'users'
    __TABLE_BOOKS = 'books'
    __TABLE_NOTES = 'notes'
    __TABLE_TASKLISTS = 'tasklists'
    __TABLE_TASKS = 'tasks'


    def __init__(self, host: str, port: int, user: str, password: str, dbname: str) -> None:

        with psycopg.connect(f'host={host} port={port} user={user} password={password}', autocommit=True) as self.__database:
            try:
                self.__database.execute(f'CREATE DATABASE "{dbname}"') # type: ignore
            except psycopg.errors.DuplicateDatabase:
                pass

        try:
            self.__database = psycopg.connect(f'host={host} port={port} user={user} password={password} dbname={dbname}', autocommit=True)
        except:
            print('database connection failed')
            sys.exit(1)

        with self.__database.cursor() as cursor:
                cursor.execute(open('sql/create_tables.sql').read()) # type: ignore


    def total_notes_count(self) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}"')
            return result[0] if (result := cursor.fetchone()) else 0


    def total_task_lists_count(self) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_TASKLISTS}"')
            return result[0] if (result := cursor.fetchone()) else 0


    def create_user(self, id: int, username: str | None, first_name: str, last_name: str | None) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO {DBHelper.__TABLE_USERS} VALUES (%s, %s, %s, %s)', (id, username, first_name, last_name))
            return True
        except:
            return False


    def get_user(self, id: int) -> User | None:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {DBHelper.__TABLE_USERS} WHERE "id" = %s', (id, ))
            return User(*result) if (result := cursor.fetchone()) else None


    def user_notes_count(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}" WHERE "owner_id" = %s', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0


    def user_books_count(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0


    def get_books(self, user_id: int) -> list[tuple[Book, int]] | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s ORDER BY "title"', (user_id, ))
                books_result = cursor.fetchall()
        except:
            return None

        books: list[tuple[Book, int]] = []

        for book in books_result:
            try:
                with self.__database.cursor() as cursor:
                    cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}" WHERE "book_id" = %s', (book[0], ))
                    count = result[0] if (result := cursor.fetchone()) else 0
            except:
                return None
            books.append((Book(*book), count))

        return books


    def create_book(self, owner_id: int, title: str) -> UUID | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_BOOKS}" ("owner_id", "title") VALUES (%s, %s)', (owner_id, title))
            return True
        except:
            return False


    def delete_book(self, owner_id: int, book_id: UUID) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s AND "id" = %s', (owner_id, book_id))
            return True
        except:
            return False


    def get_notes(self, owner_id: int, book_id: UUID) -> list[Note] | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{DBHelper.__TABLE_NOTES}" WHERE "book_id" = %s', (book_id, ))
                return [Note(*i) for i in cursor.fetchall()]
        except:
            return None


    def create_note(self, owner_id: int, book_id: UUID, title: str, text: str) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_NOTES}" ("book_id", "title", "text") VALUES (%s, %s, %s)', (book_id, title, text))
        except:
            return False
        return True


    def delete_note(self, owner_id: int, book_id: UUID, note_id: UUID) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{DBHelper.__TABLE_NOTES}" WHERE "book_id" = %s AND "note_id" = %s', (book_id, note_id))
        except:
            return False
        return True


    def get_tasklists(self, owner_id: int) -> list[TaskList] | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{DBHelper.__TABLE_TASKLISTS}" WHERE "owner_id" = %s', (owner_id, ))
                tasklists_result = cursor.fetchall()
        except:
            return None

        tasklists: list[TaskList] = []
        for tasklist in tasklists_result:
            tasklists.append(TaskList(*tasklist))

        return tasklists


    def create_tasklist(self, owner_id: int, title: str, tasks: list[str]) -> bool:
        try:
            with self.__database.cursor() as cursor:
                uuid = uuid4()
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_TASKLISTS}" ("id", "owner_id", "title") VALUES (%s, %s, %s)', (uuid, owner_id, title))
                for task in tasks:
                    cursor.execute(f'INSERT INTO {DBHelper.__TABLE_TASKS} ("tasklist_id", "text", "is_done") VALUES (%s, %s, %s)', (uuid, task, False))
        except Exception as e:
            print(e)
            return False
        return True


    def __del__(self):
        self.__database.close()
