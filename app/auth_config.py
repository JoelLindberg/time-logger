import os

from authlib.integrations.starlette_client import OAuth


oauth = OAuth()
oauth.register(
    "auth0",
    client_id=os.environ.get('CLIENT_ID'),
    client_secret=os.environ.get('CLIENT_SECRET'),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ.get('DOMAIN')}/.well-known/openid-configuration'
)
