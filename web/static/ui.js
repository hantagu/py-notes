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

    if ('auth_token' in sessionStorage)
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
        case '/notes':
            books.firstChild.classList.add('active');
            break;
        case '/task_lists':
            task_lists.firstChild.classList.add('active');
            break;
    }
});


const create_book_list_item = (book, notes_amount, on_view, on_delete) =>
{
    const card = document.createElement('div');
    card.classList.add('card', 'mt-4');

    const card_header = document.createElement('div');
    card_header.classList.add('card-header');
    card_header.innerText = book.title;

    const card_body = document.createElement('div');
    card_body.classList.add('card-body');
    card_body.innerText = `Заметок: ${notes_amount}`;

    const card_footer = document.createElement('div');
    card_footer.classList.add('card-footer');

    const button_view = document.createElement('button');
    button_view.classList.add('btn', 'btn-outline-success');
    button_view.innerText = 'Просмотр';
    button_view.addEventListener('click', on_view);
    card_footer.append(button_view);

    const button_delete = document.createElement('button');
    button_delete.classList.add('btn', 'btn-outline-danger', 'ms-2');
    button_delete.innerText = 'Удалить';
    button_delete.addEventListener('click', on_delete(card));
    card_footer.append(button_delete);

    card.append(card_header);
    card.append(card_body);
    card.append(card_footer);

    return card;
}


const create_note_list_item = (note, on_delete) =>
{
    const card = document.createElement('div');
    card.classList.add('card', 'mt-4');

    const card_header = document.createElement('div');
    card_header.classList.add('card-header');
    card_header.innerText = note.title;

    const card_body = document.createElement('div');
    card_body.classList.add('card-body');
    card_body.innerText = note.text;

    const card_footer = document.createElement('div');
    card_footer.classList.add('card-footer');

    const button_delete = document.createElement('button');
    button_delete.classList.add('btn', 'btn-outline-danger');
    button_delete.innerText = 'Удалить';
    button_delete.addEventListener('click', on_delete(card));
    card_footer.append(button_delete);

    card.append(card_header);
    card.append(card_body);
    card.append(card_footer);

    return card;
}


const show_alert = message =>
{
    const alert = document.createElement('div');
    alert.classList.add('alert', 'alert-danger', 'alert-dismissible', 'mb-4');
    alert.innerText = message;

    const button_close = document.createElement('button');
    button_close.type = 'button';
    button_close.classList.add('btn-close');
    button_close.dataset.bsDismiss = 'alert';
    alert.append(button_close);

    setTimeout(() => {
        alert.remove();
    }, 10_000);

    document.getElementById('alerts').prepend(alert);
}
