from datetime import datetime
from dateutil import tz

class Logger:
  def __init__(self, toPrint = False):
    self.toPrint = toPrint

  def log(self, message, verbose = True):
    tzlocal = tz.tzoffset('IST', 19800)
    utcnow = datetime.utcnow().replace(tzinfo=tz.tzutc())
    currTime = str(utcnow.astimezone(tzlocal).strftime("%d/%m/%Y, %I:%M:%S %p"))
    formatedMessage = '{} :: {}'.format(currTime, message)
    open('logs.txt','a+').write(formatedMessage + '\n')
    if self.toPrint:
      print(formatedMessage)

