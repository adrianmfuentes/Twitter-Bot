"""Twitter/X access layer built on Tweepy's v2 Client.

Notes on X API access tiers: the Free tier only allows posting/deleting/liking
your own content. Search, timelines and follow endpoints require at least the
Basic tier. Calls that are rejected for access-tier reasons raise
`ApiAccessError` with a message the UI can show directly to the user instead
of crashing.
"""
import logging
from dataclasses import dataclass
from typing import Callable, Optional

import tweepy

from .errors import ApiAccessError, AuthError, RateLimitError, TwitterBotError

logger = logging.getLogger(__name__)


@dataclass
class TweetResult:
    tweet_id: str
    ok: bool
    error: Optional[str] = None


class TwitterModel:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        auth = tweepy.OAuth1UserHandler(
            consumer_key, consumer_secret, access_token, access_token_secret
        )
        # Only used for media upload, which v2 still lacks a native endpoint for.
        self._api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
        self._client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )
        self.me = None

    @staticmethod
    def _wrap(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except tweepy.Unauthorized as e:
            raise AuthError("Credenciales inválidas o expiradas.") from e
        except tweepy.Forbidden as e:
            raise ApiAccessError(
                "Tu nivel de acceso a la API de X no permite esta acción."
            ) from e
        except tweepy.TooManyRequests as e:
            raise RateLimitError(
                "Límite de peticiones alcanzado. Intenta de nuevo en unos minutos."
            ) from e
        except tweepy.NotFound as e:
            raise TwitterBotError("El recurso solicitado no existe.") from e
        except tweepy.TweepyException as e:
            raise TwitterBotError(str(e)) from e

    def _require_login(self):
        if self.me is None:
            raise AuthError("Debes iniciar sesión primero.")

    # -- Auth -----------------------------------------------------------
    def verify_credentials(self):
        response = self._wrap(self._client.get_me)
        if not response or not response.data:
            raise AuthError("No se pudo verificar la cuenta.")
        self.me = response.data
        return self.me

    # -- Compose ----------------------------------------------------------
    def tweet(self, message: str, media_path: Optional[str] = None):
        self._require_login()
        media_ids = None
        if media_path:
            media = self._wrap(self._api_v1.media_upload, media_path)
            media_ids = [media.media_id]
        return self._wrap(self._client.create_tweet, text=message, media_ids=media_ids)

    def delete_tweet(self, tweet_id: str):
        self._require_login()
        return self._wrap(self._client.delete_tweet, tweet_id)

    # -- Timeline / search --------------------------------------------------
    def get_recent_tweets(self, max_results: int = 10):
        self._require_login()
        response = self._wrap(
            self._client.get_users_tweets,
            id=self.me.id,
            max_results=max_results,
            tweet_fields=["created_at", "public_metrics"],
        )
        return response.data or []

    def search_tweets(self, query: str, max_results: int = 10):
        self._require_login()
        response = self._wrap(
            self._client.search_recent_tweets,
            query=query,
            max_results=max_results,
            tweet_fields=["created_at", "author_id"],
        )
        return response.data or []

    # -- Engagement -------------------------------------------------------
    def like_tweet(self, tweet_id: str):
        self._require_login()
        return self._wrap(self._client.like, tweet_id)

    def retweet(self, tweet_id: str):
        self._require_login()
        return self._wrap(self._client.retweet, tweet_id)

    def like_tweets_by_keyword(
        self,
        keyword: str,
        count: int = 10,
        on_result: Optional[Callable[[TweetResult], None]] = None,
    ) -> list[TweetResult]:
        """Search for `keyword` and like up to `count` tweets.

        A single tweet failing (already liked, protected account, etc.)
        does not abort the rest of the batch.
        """
        tweets = self.search_tweets(keyword, max_results=count)
        results = []
        for t in tweets:
            try:
                self.like_tweet(t.id)
                result = TweetResult(tweet_id=str(t.id), ok=True)
            except TwitterBotError as e:
                result = TweetResult(tweet_id=str(t.id), ok=False, error=str(e))
            results.append(result)
            if on_result:
                on_result(result)
        return results

    # -- Follow management --------------------------------------------------
    def _resolve_user_id(self, username: str) -> str:
        response = self._wrap(self._client.get_user, username=username.lstrip("@"))
        if not response or not response.data:
            raise TwitterBotError(f"El usuario @{username} no existe.")
        return response.data.id

    def follow_user(self, username: str):
        self._require_login()
        user_id = self._resolve_user_id(username)
        return self._wrap(self._client.follow_user, self.me.id, user_id)

    def unfollow_user(self, username: str):
        self._require_login()
        user_id = self._resolve_user_id(username)
        return self._wrap(self._client.unfollow_user, self.me.id, user_id)
