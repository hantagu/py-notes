const METHOD_CREATE_BOOK = 'create_book'
const METHOD_DELETE_BOOK = 'delete_book'

const METHOD_CREATE_NOTE = 'create_note'
const METHOD_DELETE_NOTE = 'delete_note'

const METHOD_CREATE_TASK_LIST = 'create_task_list'
const METHOD_DELETE_TASK_LIST = 'delete_task_list'

const METHOD_LOGIN = 'login'
const METHOD_GET_ME = 'get_me'
const METHOD_GET_STATISTICS = 'get_statistics'


async function make_request(method, arguments)
{
    let response = await fetch(`/method/${method}`, {
        method: 'POST',
        headers: {
            'X-Notes-Auth-Token': method != METHOD_LOGIN? sessionStorage.getItem('auth_token') : null,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(arguments? arguments : {})
    });

    return response;
}
