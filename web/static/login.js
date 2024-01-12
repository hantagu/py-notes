async function on_telegram_auth(user)
{
    let response = await fetch('/method/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(user)
    });

    if (!response.ok)
    {
        alert(`HTTP Error ${response.status}: ${response.statusText}`);
        return;
    }

    let json_response = await response.json();

    if (!json_response.ok)
    {
        alert(`API Error: ${json_response.description}`);
        return;
    }

    sessionStorage.setItem('auth_token', json_response.result.auth_token);
    document.dispatchEvent(new Event('navbar'));
}
