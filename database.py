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

    def __init__(self, id: UUID, task_list_id: UUID, title: str, is_done: bool) -> None:
        self.id = id
        self.task_list_id = task_list_id
        self.title = title
        self.is_done = is_done


class DBHelper:

    __TABLE_USERS = 'users'
    __TABLE_BOOKS = 'books'
    __TABLE_NOTES = 'notes'
    __TABLE_TASK_LISTS = 'task_lists'
    __TABLE_TASKS = 'tasks'


    def __db_connect(self, host: str, port: int, user: str, password: str, dbname: str | None = None):
        if dbname:
            self.__database = psycopg.connect(f'host={host} port={port} user={user} password={password} dbname={dbname}', autocommit=True)
        else:
            self.__database = psycopg.connect(f'host={host} port={port} user={user} password={password}', autocommit=True)


    def __init__(self, host: str, port: int, user: str, password: str, dbname: str) -> None:

        self.__db_connect(host, port, user, password)
        try:
            self.__database.execute(f'CREATE DATABASE "{dbname}"') # type: ignore
        except psycopg.errors.DuplicateDatabase:
            pass

        self.__db_connect(host, port, user, password, dbname)

        with self.__database.cursor() as cursor:
            cursor.execute(open('sql/create_tables.sql').read()) # type: ignore


    def total_notes_amount(self) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}"')
            return result[0] if (result := cursor.fetchone()) else 0

    def total_task_lists_amount(self) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_TASK_LISTS}"')
            return result[0] if (result := cursor.fetchone()) else 0


    def get_user(self, id: int) -> User | None:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{DBHelper.__TABLE_USERS}" WHERE "id" = %s', (id, ))
            return User(*result) if (result := cursor.fetchone()) else None

    def create_user(self, id: int, username: str | None, first_name: str, last_name: str | None) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_USERS}" VALUES (%s, %s, %s, %s)', (id, username, first_name, last_name))
            return True
        except:
            return False


    def user_books_amount(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0

    def user_task_lists_amount(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_TASK_LISTS}" WHERE "owner_id" = %s', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0


    def get_books(self, user_id: int) -> list[tuple[Book, int]] | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'''
                    SELECT "{DBHelper.__TABLE_BOOKS}".*, COUNT("{DBHelper.__TABLE_NOTES}"."id") AS "notes_amount"
                    FROM "{DBHelper.__TABLE_BOOKS}" LEFT JOIN "{DBHelper.__TABLE_NOTES}" ON "{DBHelper.__TABLE_BOOKS}"."id" = "{DBHelper.__TABLE_NOTES}"."book_id"
                    WHERE "{DBHelper.__TABLE_BOOKS}"."owner_id" = %s
                    GROUP BY "{DBHelper.__TABLE_BOOKS}"."id"
                    ORDER BY "{DBHelper.__TABLE_BOOKS}"."title"
                ''', (user_id, ))
                books_result = cursor.fetchall()
        except:
            return None

        books: list[tuple[Book, int]] = []
        for book in books_result:
            (id, owner_id, title, notes_amount) = book
            books.append((Book(id, owner_id, title), notes_amount))

        return books

    def create_book(self, owner_id: int, title: str) -> UUID | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'''
                    INSERT INTO "${self.__TABLE_BOOKS}" ("owner_id", "title")
                    VALUES (%s, %s)
                    RETURNING "id"
                ''', (owner_id, title))
                return UUID(result[0]) if (result := cursor.fetchone()) else None
        except:
            return None

    def delete_book(self, owner_id: int, book_id: UUID) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s AND "id" = %s', (owner_id, book_id))
            return True
        except:
            return False


    def get_notes(self, owner_id: int, book_id: UUID) -> list[Note] | None:
        pass

    def create_note(self, owner_id: int, book_id: UUID, title: str, text: str) -> UUID | None:
        pass

    def delete_note(self, owner_id: int, book_id: UUID, note_id: UUID) -> bool:
        pass


    def get_task_lists(self, owner_id: int) -> list[TaskList] | None:
        pass

    def create_task_list(self, owner_id: int, title: str, tasks: list[str]) -> UUID | None:
        pass

    def delete_task_list(self, owner_id: int, task_list_id: UUID) -> bool:
        pass


    def __del__(self):
        self.__database.close()
