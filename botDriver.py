from instabot import Instabot
from constants import *
import time
import json
import random

class BotDriver:
  def __init__(self):
    self.instabot = Instabot()
    self.unfollowTime = 259200 # 3 days in seconds
    self.maxFollowingFollowerRatio = 3
    followers_following_count = self.instabot.get_followers_following_info()
    self.followers = followers_following_count['followers']
    self.following = followers_following_count['following']
    self.oldestFollowedAccountTime = self.getOldestFollowedAccount()
  def begin(self):
    while(True):
      didSomething = False
      oldestAccountTimeDiff = self.instabot.parse_string_to_time(self.instabot.get_current_time()) - self.oldestFollowedAccountTime
      if oldestAccountTimeDiff.seconds >= self.unfollowTime:
        self.instabot.unfollow_accounts(self.unfollowTime)
        oldestFollowedAccount = self.getOldestFollowedAccount()
        didSomething = True
      else:
        self.instabot.logger.log("Nothing to unfollow in given time range, time required {}".format(self.unfollowTime - oldestAccountTimeDiff.seconds))
      self.instabot.logger.log("Current following follower ratio {}".format(self.following/self.followers))
      if self.following/self.followers <= self.maxFollowingFollowerRatio:
        self.instabot.begin_following(seedAccount = SEED_ACCOUNTS[int(random.random()*1000000) % len(SEED_ACCOUNTS)])
        didSomething = True
      else:
        self.instabot.logger.log("Can't follow accounts, ratio {}".format(self.following/self.followers))
      if not didSomething:
        sleeptime = self.unfollowTime - oldestAccountTimeDiff.seconds
        self.instabot.logger.log("Didn't do anything in this iteration, sleeping for {} minutes".format(int(sleeptime/60)))
        time.sleep(sleeptime)
      followers_following_count = self.instabot.get_followers_following_info()
      self.followers = followers_following_count['followers']
      self.following = followers_following_count['following']

  def getOldestFollowedAccount(self):
    self.instabot.fetch_following()  #json.loads(open('following.txt','r').read())
    oldestFollowedAccountTime = self.instabot.parse_string_to_time(self.instabot.get_current_time())
    for id in self.instabot.following.keys():
      if self.instabot.following[id]['status'] != 1:
        oldestFollowedAccountTime = min(oldestFollowedAccountTime, self.instabot.parse_string_to_time(self.instabot.following[id]['time']))
    return oldestFollowedAccountTime
