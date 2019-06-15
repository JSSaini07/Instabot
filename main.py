import requests
import time
import json
from accountDetails import accountDetails
from constants import *

class Instabot:

  def __init__(self):
    self.accountDetails = accountDetails()
    self.isLoggedIn = False
    self.session = requests.Session()
    self.following = {}
    self.sleeptime = 10

  def login(self):
    self.session.headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
    self.session.cookies.set('ig_pr', '1')
    self.session.headers.update({'Referer': BASE_URL, 'user-agent': 'Instagram 52.0.0.8.83 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15'})
    self.session.headers.update({'X-CSRFToken': self.session.get(BASE_URL).cookies['csrftoken']})
    login_data = {'username': self.accountDetails.username, 'password': self.accountDetails.password}
    login_req = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
    self.session.headers.update({'X-CSRFToken': login_req.cookies['csrftoken']})
    if login_req.status_code == 200:
      print('Succesfully logged in')
      self.isLoggedIn = True
    else:
      print("Couldn't log in")
      self.isLoggedIn = False
    return self.isLoggedIn


  def fetch_following(self, delete_existing_following = False):

    self.following = {}
    self.sleeptime = 60

    # check if following data is already present, can be overriden using delete_existing_following param
    existing_following = open('following.txt','r').read()
    if (not delete_existing_following) and existing_following:
      print('existing following data present in following.txt, use force mode or delete the file')
      self.following = json.loads(open('following.txt','r').read())
      return

    # check for login
    if not (self.isLoggedIn or self.login()):
      return

    # get single following page data
    def get_following_single_page(after = ''):
      queryHash = self.accountDetails.following['queryHash']
      id = self.accountDetails.following['id']
      url = FOLLOWING_URL + '?query_hash={}&variables=%7B%22id%22%3A%22{}%22%2C%22include_reel%22%3Atrue%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A50%2C%22after%22%3A%22{}%22%7D'.format(queryHash, id, after)
      print('fetching url={}'.format(url))
      partialFollowing = self.session.get(url)
      return partialFollowing

    after = ''
    done = False
    while after != None:
      partialFollowing = get_following_single_page(after)
      if partialFollowing.status_code != 200:
        self.sleeptime = self.sleeptime * 2
        print('Error: Status {} Increasing sleeptime to {}, could not fetch followings for url = {}'.format(partialFollowing.status_code, self.sleeptime, url))
      else:
        self.sleeptime = 60
        print('Successfully fetched following, Decreasing sleeptime to {}'.format(self.sleeptime))
        data = partialFollowing.json()['data']['user']['edge_follow']
        after = data['page_info']['end_cursor']
        for d in data['edges']:
          self.following[d['node']['id']] = 1
      print('sleeping for {}'.format(self.sleeptime))
      time.sleep(self.sleeptime)
    open('following.txt','w').write(json.dumps(self.following))


  def unfollow_all(self):

    if not (self.isLoggedIn or self.login()):
      return
    
    self.fetch_following()

    self.sleeptime = 10
    maxsleeptime = 160

    def try_unfollow(id):
      unfollow = self.session.post(UNFOLLOW_URL.format(id), allow_redirects=True)
      return unfollow

    followingKeys = [t for t in self.following.keys()]
    for id in followingKeys:
      unfollow_req = try_unfollow(id)
      if unfollow_req.status_code != 200:
        self.sleeptime = min(self.sleeptime * 2, maxsleeptime)
        print('Error: Status {} Increasing sleeptime to {}, could not unfollow id = {}'.format(unfollow_req.status_code, self.sleeptime, id))
      else:
        self.sleeptime = max(10, self.sleeptime/2)
        print('Successfully unfollowed id = {}, Decreasing sleeptime to {}'.format(id, self.sleeptime))
        self.following.pop(id)
        open('following.txt','w').write(json.dumps(self.following))
      print('sleeping for {}'.format(self.sleeptime))
      time.sleep(self.sleeptime)
    print('Exhausted following list')


  def begin_following(self, seedAccount = 'footballsoccerplanet'):
    if not seedAccount:
      print('No seed account found')
      return
    
    if not (self.isLoggedIn or self.login()):
      return

    accountReq = self.session.get(BASE_URL + '/' + seedAccount)
    if accountReq.status_code != 200:
      print('Could not retrieve account info, status code: {}'.format(accountReq.status_code))
      return

    profileId = accountReq.text.split('profilePage_')[1].split('"')[0]
    print("Found the profile id {}".format(profileId))

  
  

