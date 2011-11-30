import tornado
from seria import NowObject, NowClient
import types

class AuthService(NowObject):
    def handle_login(self, username, password, callback):
        print '\n\n\nLOGIN CALLBACK', callback
        if callback:
            callback( Private(self) )

class Private(NowObject):
    def handle_detonate(self):
        print 'DETONATING'

def main():
    now = NowClient()

    now.local['auth'] = AuthService

    def got_login(result):
        print 'CALLING DETONATE', result
        result.detonate()

    def joined_workerpool(result):
        print 'JOINED', result
        now.auth.login('enki', 'secret', got_login)
    
    now.system.join_workerpool('auth', joined_workerpool)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()

