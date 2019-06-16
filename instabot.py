import requests
import time
import json
from datetime import datetime
from dateutil import tz
from logger import Logger
from accountDetails import accountDetails
from constants import *

class Instabot:

  def __init__(self):
    self.accountDetails = accountDetails()
    self.isLoggedIn = False
    self.session = requests.Session()
    self.following = {}
    self.sleeptime = 10
    self.logger = Logger(toPrint = True)
    self.logger.log('------------ Starting up ------------')

  def login(self):
    self.session.headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
    self.session.cookies.set('ig_pr', '1')
    self.session.headers.update({'Referer': BASE_URL, 'user-agent': 'Instagram 52.0.0.8.83 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15'})
    self.session.headers.update({'X-CSRFToken': self.session.get(BASE_URL).cookies['csrftoken']})
    login_data = {'username': self.accountDetails.username, 'password': self.accountDetails.password}
    login_req = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
    self.session.headers.update({'X-CSRFToken': login_req.cookies['csrftoken']})
    if login_req.status_code == 200:
      self.logger.log('Succesfully logged in')
      self.isLoggedIn = True
    else:
      self.logger.log("Couldn't log in")
      self.isLoggedIn = False
    return self.isLoggedIn


  def fetch_following(self):
    try:
      self.following = json.loads(open('following.txt','r').read())
    except:
      self.following = {}

    self.sleeptime = 60

    # check for login
    if not (self.isLoggedIn or self.login()):
      return

    # get single following page data
    def get_following_single_page(after = ''):
      queryHash = self.accountDetails.following['queryHash']
      id = self.accountDetails.following['id']
      url = FOLLOWING_URL + '?query_hash={}&variables=%7B%22id%22%3A%22{}%22%2C%22include_reel%22%3Atrue%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A50%2C%22after%22%3A%22{}%22%7D'.format(queryHash, id, after)
      self.logger.log('fetching url={}'.format(url))
      partialFollowing = self.session.get(url)
      return partialFollowing

    after = ''
    done = False
    while after != None:
      partialFollowing = get_following_single_page(after)
      if partialFollowing.status_code != 200:
        self.sleeptime = self.sleeptime * 2
        self.logger.log('Error: Status {} Increasing sleeptime to {}, could not fetch followings for url = {}'.format(partialFollowing.status_code, self.sleeptime, partialFollowing.url))
      else:
        self.sleeptime = 60
        self.logger.log('Successfully fetched following, Decreasing sleeptime to {}'.format(self.sleeptime))
        data = partialFollowing.json()['data']['user']['edge_follow']
        after = data['page_info']['end_cursor']
        for d in data['edges']:
          accountObj = {'time': self.get_current_time(), 'status': 1}
          self.following[d['node']['id']] =  self.following.get(d['node']['id'], accountObj)
      self.logger.log('sleeping for {}'.format(self.sleeptime))
      time.sleep(self.sleeptime)
    open('following.txt','w').write(json.dumps(self.following))


  def unfollow_accounts(self, timeDiff = 259200):

    if not (self.isLoggedIn or self.login()):
      return
    
    self.fetch_following()

    self.sleeptime = 10
    maxsleeptime = 160

    def try_unfollow(id):
      unfollow = self.session.post(UNFOLLOW_URL.format(id), allow_redirects=True)
      return unfollow

    accountsToUnfollow = []
    currTime = self.parse_string_to_time(self.get_current_time())
    for id in self.following.keys():
      followTime = self.parse_string_to_time(self.following[id]['time'])
      diffTime = currTime - followTime
      if diffTime.seconds > timeDiff:
        accountsToUnfollow.append(id)

    for id in accountsToUnfollow:
      unfollow_req = try_unfollow(id)
      if unfollow_req.status_code != 200:
        self.sleeptime = min(self.sleeptime * 2, maxsleeptime)
        self.logger.log('Error: Status {} Increasing sleeptime to {}, could not unfollow id = {}'.format(unfollow_req.status_code, self.sleeptime, id))
      else:
        self.sleeptime = max(10, self.sleeptime/2)
        self.logger.log('Successfully unfollowed id = {}, Decreasing sleeptime to {}'.format(id, self.sleeptime))
        self.following[id]['status'] = -1
        open('following.txt','w').write(json.dumps(self.following))
      self.logger.log('sleeping for {}'.format(self.sleeptime))
      time.sleep(self.sleeptime)
    self.logger.log('Exhausted following list')


  def begin_following(self, seedAccount = 'footballsoccerplanet', maxToFollow = 100):
    
    self.sleeptime = 60
    followedCount = 0
    after = ''

    if not seedAccount:
      self.logger.log('No seed account found')
      return
    
    if not (self.isLoggedIn or self.login()):
      return

    self.logger.log('Will start following accounts from seedAccount {}, maxToFollow {}'.format(seedAccount, maxToFollow))

    accountReq = self.session.get(BASE_URL + '/' + seedAccount)
    if accountReq.status_code != 200:
      self.logger.log('Could not retrieve account info, status code: {}'.format(accountReq.status_code))
      return

    profileId = accountReq.text.split('profilePage_')[1].split('"')[0]
    self.logger.log("Found the profile id {}".format(profileId))

    # get followers on single page
    def get_followers_single_page(after = ''):
      queryHash = self.accountDetails.follower['queryHash']
      url = FOLLOWER_URL + '?query_hash={}&variables=%7B%22id%22%3A%22{}%22%2C%22include_reel%22%3Atrue%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A50%2C%22after%22%3A%22{}%22%7D'.format(queryHash, profileId, after)
      self.logger.log('fetching url={}'.format(url))
      partialFollowing = self.session.get(url)
      return partialFollowing

    while after != None and followedCount < maxToFollow:
      follower_req = get_followers_single_page(after)
      if follower_req.status_code != 200:
        self.sleeptime = self.sleeptime * 2
        self.logger.log('Error: Status {} Increasing sleeptime to {}, could not fetch followers for url = {}'.format(follower_req.status_code, self.sleeptime, follower_req.url))
      else:
        self.sleeptime = 60
        self.logger.log('Successfully fetched following, Decreasing sleeptime to {}'.format(self.sleeptime))
        data= follower_req.json()['data']['user']['edge_followed_by']
        ids = [t['node']['id'] for t in data['edges']]
        totalfollowed = self.follow_accounts(ids)
        followedCount = followedCount + totalfollowed
        after = data['page_info']['end_cursor']
        self.logger.log('sleeping for {}'.format(self.sleeptime))
      time.sleep(self.sleeptime)

  # follow accounts given list of ids
  def follow_accounts(self, data = []):

    self.sleeptime = 10
    maxsleeptime = 160
    
    if not (self.isLoggedIn or self.login()):
      return

    self.logger.log('Trying to follow_accounts, total accounts given {}'.format(len(data)))
    for id in data:
      if self.following.get(id, 0):
        self.logger.log('Id {} is already present in following list, skipping this id')
      else:  
        follow_req = self.session.post(FOLLOW_ACCOUNT.format(id), allow_redirects = True)
        if follow_req.status_code != 200:
          self.sleeptime = min(self.sleeptime * 2, maxsleeptime)
          self.logger.log('Error: Status {} Increasing sleeptime to {}, could not follow id = {}'.format(follow_req.status_code, self.sleeptime, id))
        else:
          self.sleeptime = max(10, self.sleeptime/2)
          self.logger.log('Successfully followed id = {}, Decreasing sleeptime to {}'.format(id, self.sleeptime))
          self.following[id] = {'time': self.get_current_time(), 'status': 0}
          open('following.txt','w').write(json.dumps(self.following))
        self.logger.log('sleeping for {}'.format(self.sleeptime))
        time.sleep(self.sleeptime)
    self.logger.log('Successfuly followed given account, total length {}'.format(len(data)))
    return len(data)

  def get_current_time(self):
    tzlocal = tz.tzoffset('IST', 19800)
    utcnow = datetime.utcnow().replace(tzinfo=tz.tzutc())
    currTime = str(utcnow.astimezone(tzlocal).strftime("%d/%m/%Y, %I:%M:%S %p"))
    return currTime

  def parse_string_to_time(self, timestamp):
    return datetime.strptime(timestamp, "%d/%m/%Y, %I:%M:%S %p")

  def get_followers_following_info(self):
    followers_following_req = self.session.get(BASE_URL + '/' + self.accountDetails.username)
    if followers_following_req.status_code != 200:
      logger.log("Couldn't fetch personal followers following info, status code {}, url {}".format(followers_following_req.status_code, followers_following_req.url))
      return
    followers_following_text = followers_following_req.text.lower()
    followers_following_text = followers_following_text.split('<meta property="og:description" content="')[1]
    followers = followers_following_text.split(' followers')[0]
    following = followers_following_text.split('followers, ')[1].split(' following')[0]
    return {'followers': int(followers), 'following': int(following)}

  
  

