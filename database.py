from datetime import datetime
import mysql.connector as mysql
from flask.sessions import SessionMixin

class User:

    def __init__(self, id: int, username: str | None, first_name: str, last_name: str | None) -> None:
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
    
    @property
    def name(self):
        return f'{self.first_name} {self.last_name}' if self.last_name else self.first_name


class DBHelper:

    __TABLE_USERS = 'users'
    __TABLE_BOOKS = 'books'
    __TABLE_NOTES = 'notes'

    def __init__(self, host: str, user: str, password: str, database: str, recreate: bool = False) -> None:

        self.__database = mysql.connect(host=host, user=user, password=password, database=database)
        self.__database.autocommit = True

        if recreate:
            cursor = self.__database.cursor()
            cursor.executemany('DROP TABLE IF EXISTS %s', (DBHelper.__TABLE_USERS, DBHelper.__TABLE_BOOKS, DBHelper.__TABLE_NOTES))
            cursor.close()

        with self.__database.cursor() as cursor:
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {DBHelper.__TABLE_USERS} (`id` INT NOT NULL AUTO_INCREMENT,   `username` VARCHAR(32),      `first_name` VARCHAR(64) NOT NULL,    `last_name` VARCHAR(64),         PRIMARY KEY (`id`))')
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {DBHelper.__TABLE_BOOKS} (`id` INT NOT NULL AUTO_INCREMENT,   `owner_id` INT NOT NULL,     `title` VARCHAR(64) NOT NULL,                                          PRIMARY KEY (`id`), FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE CASCADE)')
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {DBHelper.__TABLE_NOTES} (`id` INT NOT NULL AUTO_INCREMENT,   `author_id` INT NOT NULL,    `book_id` INT NOT NULL,               `title` VARCHAR(64) NOT NULL,    PRIMARY KEY (`id`), FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,   FOREIGN KEY (`book_id`) REFERENCES `books` (`id`) ON DELETE CASCADE)')


    def auth(self, data: dict) -> User | None:

        if not all((auth_date := data.get('auth_date', None), id := data.get('id', None), first_name := data.get('first_name', None))):
            return None

        auth_date = int(auth_date)
        id = int(id)

        d = datetime.utcnow().timestamp() - auth_date
        if d > 3600:
            return None

        try:

            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT * FROM {DBHelper.__TABLE_USERS} WHERE `id` = %s', (id, ))
                result = cursor.fetchone()

            if (result):
                return User(result[0], result[1], result[2], result[3])

        except:
            return None

        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'INSERT INTO {DBHelper.__TABLE_USERS} VALUES (%s, %s, %s, %s)', (id, data.get('username', None), first_name, data.get('last_name', None)))
        except:
            return None
        
        return User(id, data.get('username', None), first_name, data.get('last_name', None))


    def total_notes_count(self) -> int:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {DBHelper.__TABLE_NOTES}')
                count = cursor.fetchone()[0]
            return count
        except:
            return 0


    def user_notes_count(self, user_id: int) -> int:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {DBHelper.__TABLE_NOTES} WHERE `author_id` = %s', (user_id, ))
                count = cursor.fetchone()[0]
            return count
        except:
            return 0


    def user_books_count(self, user_id: int) -> int:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {DBHelper.__TABLE_BOOKS} WHERE `owner_id` = %s', (user_id, ))
                count = cursor.fetchone()[0]
            return count
        except:
            return 0


    def get_books(self, user_id: int) -> list | None:

        try:
            with self.__database.cursor() as cursor:
                cursor.execute(f'SELECT * FROM {DBHelper.__TABLE_BOOKS} WHERE `owner_id` = %s ORDER BY `title`', (user_id, ))
                books_result = cursor.fetchall()
        except:
            return None

        result = []

        for book in books_result:
            try:
                with self.__database.cursor() as cursor:
                    cursor.execute(f'SELECT COUNT(*) FROM {DBHelper.__TABLE_NOTES} WHERE `author_id` = %s AND `book_id` = %s', (user_id, book[0]))
                    notes_count = cursor.fetchone()[0]
            except:
                return None

            result.append((book[0], book[2], notes_count))

        return result


    def create_book(self, owner_id: int, title: str) -> bool:
        try:
            with self.__database.cursor() as cursor:
                cursor.execute('INSERT INTO `books` (`owner_id`, `title`) VALUES (%s, %s)', (owner_id, title))
        except:
            return False

        return True


    def __del__(self):
        self.__database.close()