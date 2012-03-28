class TcpDummy():
  def __init__(*args):
      return
  
  def send(self, *args):
      self.last_send = args
