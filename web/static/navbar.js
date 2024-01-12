document.addEventListener('DOMContentLoaded', () =>
{
    document.dispatchEvent(new Event('navbar'));
});


document.addEventListener('navbar', () =>
{
    let main = document.getElementById('tab_main');
    let books = document.getElementById('tab_books');
    let task_lists = document.getElementById('tab_task_lists');
    let login = document.getElementById('telegram-login-T6h4dWpVNnbot');
    let logout = document.getElementById('tab_logout');

    if (sessionStorage.getItem('auth_token'))
    {
        main.style.display = '';
        books.style.display = '';
        task_lists.style.display = '';

        login.style.display = 'none';
        logout.style.display = '';
    }
    else
    {
        main.style.display = '';
        books.style.display = 'none';
        task_lists.style.display = 'none';

        login.style.display = '';
        logout.style.display = 'none';
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
