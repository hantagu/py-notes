const onTelegramAuth = async (user) =>
{
    let response = await fetch('/method/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(user)
    });

    if (!response.ok) {
        alert(`HTTP Error ${response.status}: ${response.statusText}`);
    }

    let json_response = await response.json();

    if (!json_response.ok) {
        alert(`API Error: ${json_response.description}`)
    }

    sessionStorage.setItem('auth_token', json_response.result.auth_token);
    document.dispatchEvent(new Event('navbar'));
}
