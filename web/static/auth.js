document.addEventListener('login', async event =>
{
    let response = await make_request(METHOD_LOGIN, event.detail);

    if (!response)
    {
        alert(`HTTP error occured`);
        return;
    }

    response = await response.json();

    if (!response.ok)
    {
        console.log(response);
        alert(`API error: ${response.description}`);
        return;
    }

    sessionStorage.setItem('auth_token', response.result.auth_token);
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
