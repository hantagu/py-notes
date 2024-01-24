document.addEventListener('auth', async event =>
{
    let response = await make_request(METHOD_LOGIN, event.detail);

    if (!response.ok)
    {
        console.error('[auth]', `HTTP Error: ${response.status} ${response.statusText}`);
        return;
    }

    let json_response = await response.json();

    if (!json_response.ok)
    {
        console.error('[auth]', `API Error: ${json_response.description}`);
        return;
    }

    sessionStorage.setItem('auth_token', json_response.result.auth_token);
    window.location.replace('/');
});


document.addEventListener('DOMContentLoaded', () =>
{
    let logout_button = document.getElementById('tab_logout').firstChild;

    logout_button.addEventListener('click', () =>
    {
        sessionStorage.removeItem('auth_token');
        window.location.replace('/');
    });
});
