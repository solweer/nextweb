from nextweb import secret

OAUTH_CONFIG = {
    "linkedin": {
        "client_id": secret.LINKEDIN_CLIENT_ID,
        "client_secret": secret.LINKEDIN_CLIENT_SECRET,
        "authorization_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "redirect_uri": "http://127.0.0.1:8000/linkedin/callback/",  
        "callback_url": secret.LINKEDIN_REDIRECT_URI,
        "scopes": [
            "openid",               
            "profile",             
            "w_member_social",       #
            "email",               
        ],
    },
}
