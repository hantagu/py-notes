const STYLE = 'style';
const DISPLAY_NONE = 'display: none !important;';

const DATA_BS_THEME = 'data-bs-theme';
const LIGHT = 'light';
const DARK = 'dark';


document.addEventListener('DOMContentLoaded', () =>
{
    if (window.matchMedia)
    {
        const html = document.querySelector('html');
        const prefersColorScheme = window.matchMedia('(prefers-color-scheme: dark)');

        if (prefersColorScheme.matches)
            html.setAttribute(DATA_BS_THEME, DARK);

        prefersColorScheme.addEventListener('change', event => {
            html.setAttribute(DATA_BS_THEME, event.matches? DARK : LIGHT);
        });
    }

    const main = document.getElementById('tab_main');
    const books = document.getElementById('tab_books');
    const task_lists = document.getElementById('tab_task_lists');
    const login = document.getElementById('telegram-login-T6h4dWpVNnbot');
    const logout = document.getElementById('tab_logout');

    if (sessionStorage.getItem('auth_token'))
    {
        main.removeAttribute(STYLE);
        books.removeAttribute(STYLE);
        task_lists.removeAttribute(STYLE);

        login.setAttribute(STYLE, DISPLAY_NONE);
        logout.removeAttribute(STYLE);
    }
    else
    {
        main.removeAttribute(STYLE);
        books.setAttribute(STYLE, DISPLAY_NONE);
        task_lists.setAttribute(STYLE, DISPLAY_NONE);

        login.removeAttribute(STYLE);
        logout.setAttribute(STYLE, DISPLAY_NONE);
    }

    switch (document.location.pathname)
    {
        case '/':
            main.firstChild.classList.add('active');
            break;
        case '/books':
            books.firstChild.classList.add('active');
            break;
        case '/task_lists':
            task_lists.firstChild.classList.add('active');
            break;
    }
});


const show_alert = message =>
{
    const alert = document.createElement('div');
    alert.classList.add('alert', 'alert-danger', 'alert-dismissible');
    alert.innerText = message;

    const button = document.createElement('button');
    button.type = 'button';
    button.classList.add('btn-close');
    button.dataset.bsDismiss = 'alert';
    alert.appendChild(button);

    document.getElementById('alerts').prepend(alert);
}
