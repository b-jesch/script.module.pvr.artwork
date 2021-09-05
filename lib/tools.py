import time

import xbmc
import xbmcaddon
import json
import requests
import re
from urllib.parse import unquote

ADDON = xbmcaddon.Addon(id='script.module.pvr.artwork')
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
LOC = ADDON.getLocalizedString
PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))

LANGUAGE = xbmc.getLanguage(xbmc.ISO_639_1)
if not LANGUAGE: LANGUAGE = "en"
DB_VERSION = '1.0.9'
DB_PREFIX = '%s.%s' % (ADDON_ID, DB_VERSION)


def jsonrpc(query):
    """
        perform a JSON-RPC query
    """
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring)))
        if 'result' in response: return response['result']
    except TypeError as e:
        xbmc.log('Error executing JSON RPC: %s' % e, xbmc.LOGERROR)
    return None


def get_json(url, params=None):
    """
        get info from a rest api
    """
    if not params: params = dict()

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        if response and response.content:
            data = json.loads(response.content)
            return data.get('results', data)

    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        xbmc.log(str(e), xbmc.LOGERROR)

    return None


def log(message, pretty_print=False, type=xbmc.LOGDEBUG):
    xbmc.log('[%s] %s' % (ADDON_ID, message), type)
    if pretty_print: print(json.dumps(pretty_print, sort_keys=True, indent=4, ensure_ascii=False))


def normalize_string(fname):
    """
        normalize string, strip all special chars
    """
    fname = fname.replace(':', ' -')
    fname = re.sub(r'[\\/*?"<>|]', '', fname).strip().rstrip('.')
    return ' '.join(fname.split())


def split_addonsetting(setting, separator):
    item = ADDON.getSetting(setting)
    if item == '':
        return []
    else:
        return item.split(separator)


def pure_channelname(channel):
    """
        reduce channel name to SD channels only
    """
    for item in [' HD', ' FHD', ' UHD', ' hd', ' fhd', ' uhd']:
        if item in channel: return channel.replace(item, '')
    return channel


def extend_dict(org_dict, new_dict, allow_overwrite=None):
    """
        Create a new dictionary with a's properties extended by b, without overwriting existing values.
    """
    return {**org_dict, **new_dict}


def parse_int(string):
    """
        helper to parse int from string without erroring on empty or misformed string
    """
    try:
        return int(string)
    except ValueError:
        return 0


def get_compare_string(text):
    """
        strip all special chars in a string for better comparing of searchresults
    """
    text = text.lower()
    text = ''.join(e for e in text if e.isalnum())
    return text


def url_unquote(url):
    """
        unquote urls, remove image scheme and trailing slashes
    """
    return unquote(url.replace('image://', '')).rstrip('/')


def convert_date(date, date_format='%Y-%m-%d'):
    dt = time.strptime(date, date_format)
    return time.strftime(xbmc.getRegion('dateshort'), dt)
