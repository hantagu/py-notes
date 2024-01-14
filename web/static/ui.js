const STYLE = 'style';
const DISPLAY_NONE = 'display: none !important;';

const DATA_BS_THEME = 'data-bs-theme';
const LIGHT = 'light';
const DARK = 'dark';


document.addEventListener('DOMContentLoaded', () =>
{
    if (window.matchMedia)
    {
        let html = document.querySelector('html');
        let prefersColorScheme = window.matchMedia('(prefers-color-scheme: dark)');

        if (prefersColorScheme.matches)
            html.setAttribute(DATA_BS_THEME, DARK);

        prefersColorScheme.addEventListener('change', event => {
            if (event.matches)
                html.setAttribute(DATA_BS_THEME, DARK);
            else
                html.setAttribute(DATA_BS_THEME, LIGHT);
        });
    }

    let main = document.getElementById('tab_main');
    let books = document.getElementById('tab_books');
    let task_lists = document.getElementById('tab_task_lists');
    let login = document.getElementById('telegram-login-T6h4dWpVNnbot');
    let logout = document.getElementById('tab_logout');

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
