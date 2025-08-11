import os

from urllib.parse import quote_plus, urlencode
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from auth_config import oauth


auth_router = APIRouter()


@auth_router.get("/login")
async def login(request: Request):
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    if 'id_token' not in request.session:
        return await oauth.auth0.authorize_redirect(
            request,
            redirect_uri=request.url_for("callback")
        )

    return RedirectResponse(url=request.url_for("index"))


@auth_router.get("/logout")
def logout(request: Request):
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    response = RedirectResponse(
        url="https://" + os.environ.get('DOMAIN')
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": request.url_for("index"),
                    "client_id": os.environ.get('CLIENT_ID'),
                },
                quote_via=quote_plus,
            )
    )
    request.session.clear()

    return response  # 👈 updated code


@auth_router.get("/callback")
async def callback(request: Request):
    """
    Callback redirect from Auth0
    """
    token = await oauth.auth0.authorize_access_token(request)
    # Store `id_token`, and `userinfo` in session
    request.session['id_token'] = token['id_token']
    request.session['userinfo'] = token['userinfo']

    return RedirectResponse(url=request.url_for("index"))
