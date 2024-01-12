document.addEventListener('DOMContentLoaded', () =>
{
    let logout_button = document.getElementById('tab_logout').firstChild;

    logout_button.addEventListener('click', () =>
    {
        sessionStorage.removeItem('auth_token');
        window.location.replace('/');
    });
});
