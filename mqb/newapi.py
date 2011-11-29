import tornado
from seria import NowObject, NowClient
import types

class AuthService(NowObject):
    def handle_login(self, username, password, callback):
        print 'LALALA'

        print 'CALLBACK', callback
        if callback:
            callback('FRED')

def main():
    now = NowClient()

    now.local['auth'] = AuthService

    def joined_workerpool(promise, result):
        print 'JOINED', promise, result
        now.auth.login('enki', 'secret', None)
    now.system.join_workerpool('auth', joined_workerpool)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()

