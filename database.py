from re import A
import sys
from uuid import UUID, uuid4
from datetime import datetime

import psycopg


class User:

    def __init__(self, id: int, username: str | None, first_name: str, last_name: str | None) -> None:
        self.id: int = id
        self.username: str | None = username
        self.first_name: str = first_name
        self.last_name: str | None = last_name


class Book:

    def __init__(self, id: UUID, owner_id: int, title: str) -> None:
        self.id: UUID = id
        self.owner_id: int = owner_id
        self.title: str = title


class Note:

    def __init__(self, id: UUID, book_id: UUID, title: str, text: str) -> None:
        self.id: UUID = id
        self.book_id: UUID = book_id
        self.title: str = title
        self.text: str = text


class TaskList:

    def __init__(self, id: UUID, owner_id: int, title: str) -> None:
        self.id: UUID = id
        self.owner_id: int = owner_id
        self.title: str = title


class Task:

    def __init__(self, id: UUID, task_list_id: UUID, title: str, is_done: bool) -> None:
        self.id: UUID = id
        self.task_list_id: UUID = task_list_id
        self.title: str = title
        self.is_done: bool = is_done


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
            cursor.execute(f'''
                SELECT COUNT(1)
                FROM "{DBHelper.__TABLE_NOTES}"
            ''')
            return result[0] if (result := cursor.fetchone()) else 0


    def total_task_lists_amount(self) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT COUNT(1)
                FROM "{DBHelper.__TABLE_TASK_LISTS}"
            ''')
            return result[0] if (result := cursor.fetchone()) else 0



    def user_books_amount(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT COUNT(1)
                FROM "{DBHelper.__TABLE_BOOKS}"
                WHERE "owner_id" = %s
            ''', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0


    def user_notes_amount(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT COUNT(1)
                FROM "{DBHelper.__TABLE_NOTES}"
                WHERE "owner_id" = %s
            ''', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0


    def user_task_lists_amount(self, user_id: int) -> int:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT COUNT(1)
                FROM "{DBHelper.__TABLE_TASK_LISTS}"
                WHERE "owner_id" = %s
            ''', (user_id, ))
            return result[0] if (result := cursor.fetchone()) else 0



    def get_user(self, id: int) -> User | None:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT *
                FROM "{DBHelper.__TABLE_USERS}"
                WHERE "id" = %s
            ''', (id, ))
            return User(*result) if (result := cursor.fetchone()) else None


    def create_user(self, id: int, username: str | None, first_name: str, last_name: str | None):
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                INSERT INTO "{DBHelper.__TABLE_USERS}"
                VALUES (%s, %s, %s, %s)
            ''', (id, username, first_name, last_name))



    def get_books(self, user_id: int) -> list[tuple[Book, int]]:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT "{DBHelper.__TABLE_BOOKS}".*, COUNT("{DBHelper.__TABLE_NOTES}"."id") AS "notes_amount"
                FROM "{DBHelper.__TABLE_BOOKS}" LEFT JOIN "{DBHelper.__TABLE_NOTES}" ON "{DBHelper.__TABLE_BOOKS}"."id" = "{DBHelper.__TABLE_NOTES}"."book_id"
                WHERE "{DBHelper.__TABLE_BOOKS}"."owner_id" = %s
                GROUP BY "{DBHelper.__TABLE_BOOKS}"."id"
                ORDER BY "{DBHelper.__TABLE_BOOKS}"."title"
            ''', (user_id, ))
            return [(Book(*row[:-1]), row[-1]) for row in cursor.fetchall()]


    def create_book(self, owner_id: int, title: str) -> Book:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                INSERT INTO "{self.__TABLE_BOOKS}" ("owner_id", "title")
                VALUES (%s, %s)
                RETURNING *
            ''', (owner_id, title))
            return Book(*cursor.fetchone()) # type: ignore


    def delete_book(self, owner_id: int, book_id: UUID) -> Book | None:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                DELETE FROM "{DBHelper.__TABLE_BOOKS}"
                WHERE "owner_id" = %s AND "id" = %s
                RETURNING *
            ''', (owner_id, book_id))
            return Book(*result) if (result := cursor.fetchone()) else None



    def get_notes(self, owner_id: int, book_id: UUID) -> list[Note]:
        self.__check_user_book_exists(owner_id, book_id)
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT *
                FROM "{DBHelper.__TABLE_NOTES}"
                WHERE "book_id" = %s
            ''', (book_id, ))
            return [Note(*result) for result in cursor.fetchall()]


    def create_note(self, owner_id: int, book_id: UUID, title: str, text: str) -> Note:
        self.__check_user_book_exists(owner_id, book_id)
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                INSERT INTO "{DBHelper.__TABLE_NOTES}" ("book_id", "title", "text")
                VALUES (%s, %s, %s)
                RETURNING *
            ''', (book_id, title, text))
            return Note(*cursor.fetchone()) # type: ignore


    def delete_note(self, owner_id: int, book_id: UUID, note_id: UUID) -> Note | None:
        self.__check_user_book_exists(owner_id, book_id)
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                DELETE FROM "{DBHelper.__TABLE_NOTES}"
                WHERE "book_id" = %s AND "id" = %s
                RETURNING *
            ''', (book_id, note_id))
            return Note(*result) if (result := cursor.fetchone()) else None



    def get_task_lists(self, owner_id: int) -> list[tuple[TaskList, list[Task]]]:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT *
                FROM "{DBHelper.__TABLE_TASK_LISTS}"
                WHERE "owner_id" = %s
            ''', (owner_id, ))
            task_lists: list[TaskList] = [TaskList(*task_lists) for task_lists in cursor.fetchall()]

        result: list[tuple[TaskList, list[Task]]] = []
        for task_list in task_lists:
            with self.__database.cursor() as cursor:
                cursor.execute(f'''
                    SELECT *
                    FROM "{DBHelper.__TABLE_TASKS}"
                    WHERE "task_list_id" = %s
                ''', (task_list.id, ))
                tasks: list[Task] = [Task(*task) for task in cursor.fetchall()]
            result.append((task_list, tasks))

        return result


    def create_task_list(self, owner_id: int, title: str, tasks: list[str]) -> tuple[TaskList, list[Task]]:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                INSERT INTO "{DBHelper.__TABLE_TASK_LISTS}" ("owner_id", "title")
                VALUES (%s, %s)
                RETURNING *
            ''', (owner_id, title))
            _tasklist: TaskList = TaskList(*cursor.fetchone()) # type: ignore

        with self.__database.cursor() as cursor:
            cursor.executemany(f'''
                INSERT INTO "{DBHelper.__TABLE_TASKS}" ("task_list_id", "text", "is_done")
                VALUES (%s, %s, %s)
                RETURNING *
            ''', [(_tasklist.id, task) for task in tasks])
            _tasks: list[Task] = [Task(*task) for task in cursor.fetchall()]

        return _tasklist, _tasks


    def delete_task_list(self, owner_id: int, task_list_id: UUID) -> TaskList | None:
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                DELETE FROM "{DBHelper.__TABLE_TASK_LISTS}"
                WHERE "owner_id" = %s AND "id" = %s
                RETURNING *
            ''', (owner_id, task_list_id))
            return TaskList(*result) if (result := cursor.fetchone()) else None



    def __check_user_book_exists(self, owner_id: int, book_id: UUID):
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT EXISTS (
                    SELECT 1
                    FROM "{DBHelper.__TABLE_BOOKS}"
                    WHERE "owner_id" = %s AND "id" = %s
                    LIMIT 1
                )
            ''', (owner_id, book_id))
            if not (result[0] if (result := cursor.fetchone()) else False):
                raise NotExistsException


    def __check_user_task_list_exists(self, owner_id: int, task_list_id: UUID):
        with self.__database.cursor() as cursor:
            cursor.execute(f'''
                SELECT EXISTS (
                    SELECT 1
                    FROM "{DBHelper.__TABLE_TASK_LISTS}"
                    WHERE "owner_id" = %s AND "id" = %s
                    LIMIT 1
                )
            ''', (owner_id, task_list_id))
            if not (result[0] if (result := cursor.fetchone()) else False):
                raise NotExistsException



    def __del__(self):
        self.__database.close()


class NotExistsException(Exception):
    pass
