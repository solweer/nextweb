from nextweb import secret

OAUTH_CONFIG = {
    "twitter": {
        "client_id": secret.TWITTER_CLIENT_ID,
        "client_secret": secret.TWITTER_CLIENT_SECRET,
        "authorization_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "redirect_uri": secret.TWITTER_REDIRECT_URI,
        "callback_url": secret.TWITTER_REDIRECT_URI,
        "scopes": [
            "tweet.read",
            "users.read",
            "offline.access",
        ],
    },
}
