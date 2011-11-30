import tornado
from seria import NowObject, NowClient
import types

def main():
    now = NowClient()
    
    def got_data(data):
        print 'GOT DATA', data

    now.webpull.fetch_url(url="http://xkcd.com/", callback=got_data)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()

