class accountDetails:
  def __init__(self):
    self.username = 'yourusername'
    self.password = 'yourpassword'
    self.following = {
      'queryHash': "queryhash in api request when fetching following data, doesn't change",
      'id': 'id associated with the following data request'
    }