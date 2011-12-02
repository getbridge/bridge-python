import tornado
from tornado import ioloop, httpclient
from seria import NowObject, NowClient
import types

class WebPullService(NowObject):
    def handle_fetch_url(self, url, callback):
        print 'FETCH', url, callback

        request = httpclient.HTTPRequest(
                    url=url,
                  )
        http_client = httpclient.AsyncHTTPClient()
        def got_result(result ):
            print result
            result and callback and callback(x.body)
        http_client.fetch(request, got_result)

def main():
    now = NowClient()

    now.local['webpull'] = WebPullService

    def joined_workerpool(result):
        print 'JOINED'
    
    now.system.join_workerpool('webpull', joined_workerpool)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()

