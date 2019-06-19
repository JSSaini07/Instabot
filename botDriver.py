from instabot import Instabot
from constants import *
import time
import json
import random

class BotDriver:
  def __init__(self, skipDataCollection = False):
    self.instabot = Instabot(skipDataCollection)
    self.unfollowTime = 172800 #259200 3 days in seconds
    self.totalFollowing = self.instabot.get_total_following()
    self.maxFollowing = 500 
    self.sleeptime = 3600
    self.tick = 0
  def begin(self):
    while(True):
      followedAccounts = False
      self.instabot.unfollow_accounts(self.unfollowTime)
      self.totalFollowing = self.instabot.get_total_following()
      self.instabot.logger.log("Current following count {}".format(self.totalFollowing))
      if self.totalFollowing <= self.maxFollowing:
        self.instabot.begin_following(seedAccount = SEED_ACCOUNTS[int(random.random()*1000000) % len(SEED_ACCOUNTS)])
        followedAccounts = True
      else:
        self.instabot.logger.log("Can't follow accounts, following count {}".format(self.totalFollowing))
      if not followedAccounts:
        self.instabot.logger.log("Didn't follow anything in this iteration, sleeping for {} minutes".format(int(self.sleeptime/60)))
        time.sleep(self.sleeptime)
      self.tick = self.tick + 1
      if self.tick % 5 == 0:
        self.instabot.logger.log("Iteration {}, updating data".format(self.tick))
        self.instabot.fetch_following()
      self.totalFollowing = self.instabot.get_total_following()
