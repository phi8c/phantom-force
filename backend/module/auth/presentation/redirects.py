from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def append_auth_result(
    configured_url: str,
    login_status: str,
    challenge_id: str | None,
) -> str:
    parts = urlsplit(configured_url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.append(("auth_status", login_status))
    if challenge_id is not None:
        query.append(("mfa_challenge_id", challenge_id))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )
