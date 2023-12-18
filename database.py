from datetime import datetime
from sqlite3 import dbapi2
import sys
from uuid import UUID
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

    def __init__(self, id: UUID, owner_id: UUID, title: str, text: str) -> None:
        self.id = id
        self.owner_id = owner_id
        self.title = title
        self.text = text


class DBHelper:

    __TABLE_USERS = 'users'
    __TABLE_BOOKS = 'books'
    __TABLE_NOTES = 'notes'


    def __init__(self, host: str, port: int, user: str, password: str, dbname: str) -> None:

        with psycopg.connect(f'host={host} port={port} user={user} password={password}', autocommit=True) as self.__database:
            try:
                self.__database.execute(f'CREATE DATABASE "{dbname}"') # type: ignore
            except psycopg.errors.DuplicateDatabase:
                pass

        try:
            self.__database = psycopg.connect(f'host={host} port={port} user={user} password={password} dbname={dbname}', autocommit=True)
        except:
            print('Не удалось соединиться с БД')
            sys.exit(1)

        with self.__database.cursor() as cursor:
                cursor.execute(open('sql/create_tables.sql').read()) # type: ignore


    def auth(self, data: dict) -> User | None:

        if not all((auth_date := data.get('auth_date', None), id := data.get('id', None), first_name := data.get('first_name', None))):
            return None

        auth_date = int(auth_date)
        id = int(id)

        if datetime.utcnow().timestamp() - auth_date > 3600:
            return None

        with self.__database.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {DBHelper.__TABLE_USERS} WHERE "id" = %s', (id, ))
            result = cursor.fetchone()

        if result:
            return User(result[0], result[1], result[2], result[3])

        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_USERS}" VALUES (%s, %s, %s, %s)', (id, data.get('username', None), first_name, data.get('last_name', None)))
        except:
            return None

        return User(id, data.get('username', None), first_name, data.get('last_name', None))


    def total_notes_count(self) -> int:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}"')
                count = result[0] if (result := cursor.fetchone()) else 0
            return count
        except:
            return 0


    def user_notes_count(self, user_id: int) -> int:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}" WHERE "owner_id" = %s', (user_id, ))
                count = result[0] if (result := cursor.fetchone()) else 0
            return count
        except:
            return 0


    def user_books_count(self, user_id: int) -> int:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s', (user_id, ))
                result = cursor.fetchone()
                count = result[0] if result else 0
            return count
        except:
            return 0


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
                    cursor.execute(f'SELECT COUNT("id") FROM "{DBHelper.__TABLE_NOTES}" WHERE "owner_id" = %s AND "book_id" = %s', (user_id, book[0]))
                    count = result[0] if (result := cursor.fetchone()) else 0
            except:
                return None
            books.append((Book(*book), count))

        return books


    def create_book(self, owner_id: int, title: str) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_BOOKS}" ("owner_id", "title") VALUES (%s, %s)', (owner_id, title))
        except:
            return False
        return True


    def delete_book(self, owner_id: int, book_id: UUID) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{DBHelper.__TABLE_BOOKS}" WHERE "owner_id" = %s AND "id" = %s', (owner_id, book_id))
        except:
            return False
        return True


    def get_notes(self, owner_id: int, book_id: UUID) -> list[Note] | None:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{DBHelper.__TABLE_NOTES}" WHERE "owner_id" = %s AND "book_id" = %s', (owner_id, book_id))
                return [Note(*i) for i in cursor.fetchall()]
        except:
            return None


    def create_note(self, owner_id: int, book_id: UUID, title: str, text: str) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{DBHelper.__TABLE_NOTES}" ("owner_id", "book_id", "title", "text") VALUES (%s, %s, %s, %s)', (owner_id, book_id, title, text))
        except:
            return False
        return True


    def delete_note(self, owner_id: int, book_id: UUID, note_id: UUID) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{DBHelper.__TABLE_NOTES}" WHERE "owner_id" = %s AND "book_id" = %s AND "note_id" = %s', (owner_id, book_id, note_id))
        except:
            return False
        return True


    def __del__(self):
        self.__database.close()
