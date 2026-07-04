import sys
import types
import unittest
from unittest.mock import MagicMock, patch

import tweepy

sys.path.insert(0, ".")

from twitter_bot.errors import AuthError, ApiAccessError, TwitterBotError
from twitter_bot.model import TwitterModel


def make_response(data):
    resp = MagicMock()
    resp.data = data
    return resp


class TwitterModelTests(unittest.TestCase):
    def _make_model(self):
        with patch("twitter_bot.model.tweepy.OAuth1UserHandler"), \
             patch("twitter_bot.model.tweepy.API"), \
             patch("twitter_bot.model.tweepy.Client") as client_cls:
            model = TwitterModel("ck", "cs", "at", "ats")
            return model, client_cls.return_value

    def test_verify_credentials_success(self):
        model, client = self._make_model()
        me = types.SimpleNamespace(id="123", username="adri")
        client.get_me.return_value = make_response(me)

        result = model.verify_credentials()

        self.assertEqual(result, me)
        self.assertEqual(model.me, me)

    def test_verify_credentials_bad_auth_raises_autherror(self):
        model, client = self._make_model()
        client.get_me.side_effect = tweepy.Unauthorized(MagicMock())

        with self.assertRaises(AuthError):
            model.verify_credentials()

    def test_tweet_without_login_raises_autherror(self):
        model, _ = self._make_model()
        with self.assertRaises(AuthError):
            model.tweet("hola mundo")

    def test_tweet_calls_create_tweet(self):
        model, client = self._make_model()
        model.me = types.SimpleNamespace(id="123")

        model.tweet("hola mundo")

        client.create_tweet.assert_called_once_with(text="hola mundo", media_ids=None)

    def test_forbidden_maps_to_apiaccesserror(self):
        model, client = self._make_model()
        model.me = types.SimpleNamespace(id="123")
        client.create_tweet.side_effect = tweepy.Forbidden(MagicMock())

        with self.assertRaises(ApiAccessError):
            model.tweet("hola mundo")

    def test_like_tweets_by_keyword_continues_after_failure(self):
        model, client = self._make_model()
        model.me = types.SimpleNamespace(id="123")
        tweets = [types.SimpleNamespace(id="1"), types.SimpleNamespace(id="2")]
        client.search_recent_tweets.return_value = make_response(tweets)
        client.like.side_effect = [tweepy.Forbidden(MagicMock()), MagicMock()]

        seen = []
        results = model.like_tweets_by_keyword("python", count=2, on_result=seen.append)

        self.assertEqual(len(results), 2)
        self.assertFalse(results[0].ok)
        self.assertTrue(results[1].ok)
        self.assertEqual(len(seen), 2)

    def test_follow_user_resolves_username_then_follows(self):
        model, client = self._make_model()
        model.me = types.SimpleNamespace(id="123")
        client.get_user.return_value = make_response(types.SimpleNamespace(id="999"))

        model.follow_user("@someone")

        client.get_user.assert_called_once_with(username="someone")
        client.follow_user.assert_called_once_with("123", "999")


if __name__ == "__main__":
    unittest.main()
