from .tools import *


class FanartTv(object):

    def __init__(self):
        self.api_key = ADDON.getSetting('fanart_apikey')

        self.endpoint = dict({'movie': 'movies', 'tvshow': 'tv'})
        self.prefix = dict({'movie': 'movie', 'tvshow': 'tv'})

        self.arttypes = dict({'fanart': 'fanart', 'thumb': 'thumb', 'banner': 'banner', 'logo': 'logo',
                              'background': 'fanart', 'landscape': 'landscape', 'poster': 'poster'})

        self.arttypes_general = dict({'disc': 'discart', 'clearlogo': 'clearlogo', 'clearart': 'clearart',
                                      'characterart': 'characterart'})

    def get_fanart_data(self, endpoint, params):
        """
            helper method to get data from fanart.tv json API
        """
        url = u'http://webservice.fanart.tv/v3/%s/%s' % (endpoint, params['id'])

        if self.api_key:
            params.update({'api_key': self.api_key})

        params.pop('id')
        return get_json(url, params, prefix=None)

    def get_fanarts(self, media_type, imdb_id):

        if not (media_type or imdb_id): return False

        params = dict({'id': imdb_id, 'lang': LANGUAGE})
        res = self.get_fanart_data(self.endpoint[media_type], params)

        if res is None or res.get('status') == 'error': return False

        artwork = dict()
        for fanart in res:
            for key in self.arttypes:
                if '%s%s' % (self.prefix[media_type], key) in fanart:
                    artwork.update({self.arttypes[key]: res[fanart][0].get('url')})
                    break

            # get general fanarts
            for key in self.arttypes_general:
                if key in fanart:
                    artwork.update({self.arttypes_general[key]: res[fanart][0].get('url')})
                    break

        return artwork
