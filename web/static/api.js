const METHOD_GET_STATISTICS = 'get_statistics';
const METHOD_GET_USER_STATISTICS = 'get_user_statistics';
const METHOD_LOGIN = 'login';
const METHOD_GET_ME = 'get_me';

const METHOD_GET_BOOKS = 'get_books';
const METHOD_CREATE_BOOK = 'create_book';
const METHOD_DELETE_BOOK = 'delete_book';

const METHOD_GET_NOTES = 'get_notes';
const METHOD_CREATE_NOTE = 'create_note';
const METHOD_DELETE_NOTE = 'delete_note';

const METHOD_GET_TASK_LISTS = 'get_task_lists';
const METHOD_CREATE_TASK_LIST = 'create_task_list';
const METHOD_DELETE_TASK_LIST = 'delete_task_list';


const make_request = (method, args) => new Promise(async (resolve, reject) =>
{
    const headers = new Headers();
    headers.set('Content-Type', 'application/json');
    if ('auth_token' in sessionStorage)
        headers.set('X-Notes-Auth-Token', sessionStorage.getItem('auth_token'));

    const response = await fetch(`/method/${method}`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(args? args : {})
    });

    let json_response;
    try {
        json_response = await response.json();
    }
    catch {
        reject({json: false, code: response.status, text: response.statusText});
        return;
    }

    if (!json_response.ok) {
        reject({json: true, description: json_response.description});
        return;
    }

    resolve(json_response.result);
});

