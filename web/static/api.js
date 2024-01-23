const METHOD_GET_STATISTICS = 'get_statistics';

const METHOD_LOGIN = 'login';
const METHOD_GET_ME = 'get_me';


async function make_request(method, arguments)
{
    let response = await fetch(`/method/${method}`, {
        method: 'POST',
        headers: {
            'X-Notes-Auth-Token': method != METHOD_LOGIN? sessionStorage.getItem('auth_token') : null,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(arguments)
    });

    return response;
}
