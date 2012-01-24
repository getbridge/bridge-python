import tornado
from seria import NowObject, NowClient
import types

def prnt(x):
    print 'PRNT', x

def main():
    now = NowClient()

    def got_resized(file):
        print 'RESIZED', file
        file.get_localpath(prnt)

    def got_file(file):
        print 'GOT FILE', file
        now.resize.resize(file, 25, 25, got_resized)

    now.webpull.fetch_url("http://flotype.com/images/shipyard.png", got_file)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()

