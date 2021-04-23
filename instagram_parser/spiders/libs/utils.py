def get_cookies(response):
    result = {}

    for string in response.headers.getlist(b"Set-Cookie"):
        b_key, b_value = string.split(b";")[0].split(b"=")
        key = b_key.decode()
        value = b_value.decode()

        if value.startswith('"'):
            value = value[1:-1]

        result.setdefault(key, "")

        if value:
            result[key] = value

    return result
