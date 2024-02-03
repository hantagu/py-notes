document.addEventListener('auth', event =>
{
    make_request(METHOD_LOGIN, event.detail)
        .then(result => {
            sessionStorage.setItem('auth_token', result.auth_token);
            window.location.replace('/');
        })
        .catch(error => {
            show_alert(error.json? `Ошибка API: ${error.description}` : `Ошибка HTTP: ${error.code} ${error.text}`);
        });
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
