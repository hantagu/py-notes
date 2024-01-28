import enum


class HTTP(enum.Enum):
    OK = 200

    BadRequest = 400
    Unauthorized = 401
    NotFound = 404

    InternalServerError = 500
    NotImplemented = 501


class Page(enum.Enum):
    Main = 'main'
    Books = 'books'
    Notes = 'notes'
    TaskLists = 'task_lists'


class Method(enum.Enum):
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
