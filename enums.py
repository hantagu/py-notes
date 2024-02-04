from enum import Enum


class HTTP(Enum):
    OK = 200

    BadRequest = 400
    Unauthorized = 401
    NotFound = 404

    InternalServerError = 500
    NotImplemented = 501


class Page(Enum):
    Main = 'main'
    Books = 'books'
    Notes = 'notes'
    TaskLists = 'task_lists'


class Method(Enum):
    GetStatistics = 'get_statistics'
    GetUserStatistics = 'get_user_statistics'
    Login = 'login'
    GetMe = 'get_me'

    GetBooks ='get_books'
    CreateBook = 'create_book'
    DeleteBook = 'delete_book'

    GetNotes ='get_notes'
    CreateNote = 'create_note'
    DeleteNote = 'delete_note'

    GetTaskLists ='get_task_lists'
    CreateTaskList = 'create_task_list'
    DeleteTaskList = 'delete_task_list'


class ErrorTexts(Enum):
    NotImplementedYet = 'not implemented yet'
    InvalidRequestFormat = 'invalid request format'

    AuthenticationHeaderNotFound = 'authentication header not found'
    InvalidTokenSignature = 'invalid token signature'
    TokenHasExpired = 'token has expired'
    InvalidToken = 'invalid token'

    DataIsNotFromTelegram = 'data is not from Telegram'
    DataIsOutdated = 'data is outdated'

    InternalServerError = 'internal server error'

    FailedToGetStatistics = 'failed to get statistics'

    NotEnoughArguments = 'not enough arguments'
    InvalidArgumentValue = 'invalid argument value'

    UserNotFound = 'user not found'
    BookNotFound = 'book not found'
    NoteNotFound = 'note not found'
