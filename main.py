import tweepy
import tkinter as tk
from tkinter import ttk, messagebox

'''
Author: Adrián Martínez Fuentes
Date: 2024-12-28
Project: Twitter Bot

Description: This is a simple Twitter bot that can send tweets, follow followers, favorite tweets by keywords, 
and more. This bot uses the Tweepy library to interact with the Twitter API. It has a simple GUI that allows 
the user to login with their Twitter API credentials and perform various actions.
It follows the MVC (Model-View-Controller) design pattern.
'''

#########################################################################################################
######################################## Bot Model ######################################################
#########################################################################################################
class TwitterModel:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)

    def verify_credentials(self):
        try:
            self.api.verify_credentials()
            return True
        except tweepy.TweepError as e:
            raise Exception(f"Authentication failed: {e.reason}")

    def tweet(self, message):
        self.api.update_status(status=message)

    def follow_followers(self):
        for follower in tweepy.Cursor(self.api.followers).items():
            follower.follow()

    def favorite_tweets(self, keywords):
        for tweet in tweepy.Cursor(self.api.search, q=keywords).items(10):
            tweet.favorite()



#########################################################################################################
######################################## Bot View #######################################################
#########################################################################################################
class TwitterBotView:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Twitter Bot Login")
        self.root.geometry("400x300")
        self.create_login_gui()

    def create_login_gui(self):
        tk.Label(self.root, text="Consumer Key:").pack(pady=5)
        self.consumer_key_entry = tk.Entry(self.root, width=40)
        self.consumer_key_entry.pack(pady=5)

        tk.Label(self.root, text="Consumer Secret:").pack(pady=5)
        self.consumer_secret_entry = tk.Entry(self.root, width=40)
        self.consumer_secret_entry.pack(pady=5)

        tk.Label(self.root, text="Access Token:").pack(pady=5)
        self.access_token_entry = tk.Entry(self.root, width=40)
        self.access_token_entry.pack(pady=5)

        tk.Label(self.root, text="Access Token Secret:").pack(pady=5)
        self.access_token_secret_entry = tk.Entry(self.root, width=40)
        self.access_token_secret_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.controller.validate_credentials).pack(pady=10)

    def create_main_gui(self):
        self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Twitter Bot")
        self.root.geometry("400x300")

        tk.Label(self.root, text="Tweet something:").pack(pady=5)
        self.tweet_entry = tk.Entry(self.root, width=40)
        self.tweet_entry.pack(pady=5)
        tk.Button(self.root, text="Send Tweet", command=self.controller.send_tweet).pack(pady=5)

        tk.Button(self.root, text="Follow Followers", command=self.controller.follow_followers).pack(pady=10)

        tk.Label(self.root, text="Favorite Tweets by Keywords:").pack(pady=5)
        self.favorite_keywords_entry = tk.Entry(self.root, width=40)
        self.favorite_keywords_entry.pack(pady=5)
        tk.Button(self.root, text="Favorite Tweets", command=self.controller.favorite_tweets).pack(pady=5)

    def show_message(self, title, message, type="info"):
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)

    def get_login_data(self):
        return {
            "consumer_key": self.consumer_key_entry.get(),
            "consumer_secret": self.consumer_secret_entry.get(),
            "access_token": self.access_token_entry.get(),
            "access_token_secret": self.access_token_secret_entry.get(),
        }

    def get_tweet_message(self):
        return self.tweet_entry.get()

    def get_favorite_keywords(self):
        return self.favorite_keywords_entry.get()



#########################################################################################################
######################################## Bot Controller #################################################
#########################################################################################################
class TwitterBotController:
    def __init__(self):
        self.view = TwitterBotView(self)

    def validate_credentials(self):
        login_data = self.view.get_login_data()
        if not all(login_data.values()):
            self.view.show_message("Warning", "All fields must be filled out!", "warning")
            return

        try:
            self.model = TwitterModel(**login_data)
            self.model.verify_credentials()
            self.view.show_message("Success", "Login successful!")
            self.view.create_main_gui()
        except Exception as e:
            self.view.show_message("Error", str(e), "error")

    def send_tweet(self):
        message = self.view.get_tweet_message()
        if not message:
            self.view.show_message("Warning", "Tweet message cannot be empty!", "warning")
            return

        try:
            self.model.tweet(message)
            self.view.show_message("Success", "Tweet sent!")
        except Exception as e:
            self.view.show_message("Error", str(e), "error")

    def follow_followers(self):
        try:
            self.model.follow_followers()
            self.view.show_message("Success", "Followed all followers!")
        except Exception as e:
            self.view.show_message("Error", str(e), "error")

    def favorite_tweets(self):
        keywords = self.view.get_favorite_keywords()
        if not keywords:
            self.view.show_message("Warning", "Keywords cannot be empty!", "warning")
            return

        try:
            self.model.favorite_tweets(keywords)
            self.view.show_message("Success", "Favorited tweets with the given keywords!")
        except Exception as e:
            self.view.show_message("Error", str(e), "error")



#########################################################################################################
######################################## Bot Main Function ##############################################
#########################################################################################################
if __name__ == '__main__':
    controller = TwitterBotController()
    controller.view.root.mainloop()
