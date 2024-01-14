const AUTH_TOKEN = 'auth_token';

const METHOD_GET_TOTAL_NOTES_AMOUNT = 'get_total_notes_amout';
const METHOD_GET_TOTAL_TASK_LISTS_AMOUNT = 'get_total_task_lists_amont';

const METHOD_LOGIN = 'login';
const METHOD_GET_ME = 'get_me';

/*
    {
        "token": "",
        "arguments": {
            "key": "value"
        }
    }

    {
        "ok": true,
        "result": {
            "key": "value"
        }
    }

    {
        "ok": false,
        "description": ""
    }
*/

async function make_request(method, arguments)
{
    let response = await fetch(`/method/${method}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            "auth_token": method != METHOD_LOGIN? sessionStorage.getItem('auth_token') : null,
            "arguments": arguments
        })
    });

    return response;
}
