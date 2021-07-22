"""
    This module is mainly inspired from the script.module.metadatautils from Marcel van der Veldt
    and other contributors. This modules use a subset from metadatautils reduced to PVR related content.
"""
import xbmcgui
import xbmcvfs
import os
from difflib import SequenceMatcher as SM
import simplecache

from tools import *
from tmdb import Tmdb

from datetime import timedelta

dict_arttypes = {'fanart': 'fanart.jpg', 'thumb': 'folder.jpg', 'discart': 'discart,jpg', 'banner': 'banner.jpg',
                 'clearlogo': 'clearlogo.png', 'clearart': 'clearart.png', 'characterart': 'characterart.png',
                 'poster': 'poster.jpg', 'landscape': 'landscape.jpg'}

if ADDON.getSetting('pvr_art_custom_path') == '':
    ADDON.setSetting('pvr_art_custom_path', PROFILE)
    log('set artwork costum path to %s' % PROFILE)


def download_artwork(folderpath, artwork):
    """
        download artwork to local folder
    """
    art = {}
    if artwork and not xbmcvfs.exists(folderpath): xbmcvfs.mkdir(folderpath)
    for item in artwork:
        for key in item:
            if key in dict_arttypes: art[key] = download_image(os.path.join(folderpath, dict_arttypes[key]), item[key])
            elif key == "fanarts":
                images = list()
                for count, image in enumerate(item[key]):
                    image = download_image(os.path.join(folderpath, "fanart%s.jpg" % str(count + 1)), image)
                    images.append(image)
                    if count >= 4:
                        break
                art[key] = images
            elif key == "posters":
                images = list()
                for count, image in enumerate(item[key]):
                    image = download_image(os.path.join(folderpath, "poster%s.jpg" % str(count + 1)), image)
                    images.append(image)
                    if count >= 4:
                        break
                art[key] = images
            else:
                art[key] = item[key]
    return art


def download_image(filename, url):
    """
        download specific image to local folder, cache image in textures.db
    """
    if not url: return url
    if xbmcvfs.exists(filename) and filename == url: return filename
    # only overwrite if new image is different
    else:
        if xbmcvfs.exists(filename): xbmcvfs.delete(filename)
        if xbmcvfs.copy(url, filename):

            # tell kodi texture cache to refresh a particular image
            import sqlite3
            dbpath = xbmcvfs.translatePath("special://database/Textures13.db")
            connection = sqlite3.connect(dbpath, timeout=30, isolation_level=None)

            try:
                cache_image = connection.execute('SELECT cachedurl FROM texture WHERE url = ?', (filename,)).fetchone()
                if cache_image and isinstance(cache_image, str):
                    if xbmcvfs.exists(cache_image):
                        xbmcvfs.delete("special://profile/Thumbnails/%s" % cache_image)
                    connection.execute('DELETE FROM texture WHERE url = ?', (filename,))
                connection.close()
            except Exception as e:
                log(str(e), xbmc.LOGERROR)
            finally:
                del connection
            return filename
    return url


def manual_set_artwork(artwork):
    """
        Allow user to manually select the artwork with a select dialog
        show dialogselect with all artwork options
    """
    changemade = False
    abort = False

    while not abort:
        listitems = list()
        for arttype in dict_arttypes:
            img = url_unquote(artwork.get(arttype, ""))
            listitem = xbmcgui.ListItem(label=arttype, label2=img)
            listitem.setArt({'icon': img})
            listitem.setProperty("icon", img)
            listitems.append(listitem)
        dialog = xbmcgui.Dialog().select(xbmc.getLocalizedString(13511), list=listitems, useDetails=True)
        if dialog == -1:
            abort = True
        else:
            # show results for selected art type
            artoptions = []
            selected_item = listitems[dialog]
            image = selected_item.getProperty("icon")
            label = selected_item.getLabel()
            subheader = "%s: %s" % (xbmc.getLocalizedString(13511), label.capitalize())
            if image:
                # current image
                listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(13512), label2=image)
                listitem.setArt({'icon': image})
                listitem.setProperty("icon", image)
                artoptions.append(listitem)
                # none option
                listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(231))
                listitem.setArt({'icon': "DefaultAddonNone.png"})
                listitem.setProperty("icon", "DefaultAddonNone.png")
                artoptions.append(listitem)

            # browse option
            listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(1024))
            listitem.setArt({'icon': "DefaultFolder.png"})
            listitem.setProperty("icon", "DefaultFolder.png")
            artoptions.append(listitem)

            # add remaining images as option
            allarts = artwork.get(label + "s", [])
            for item in allarts:
                listitem = xbmcgui.ListItem(label=item)
                listitem.setArt({'icon': item})
                listitem.setProperty("icon", item)
                artoptions.append(listitem)

            dialog = xbmcgui.Dialog().select(subheader, list=artoptions, useDetails=True)
            if image and dialog == 1:
                # set image to None
                artwork[label] = ""
                changemade = True
            elif (image and dialog > 2) or (not image and dialog > 0):
                # one of the optional images is selected as new default
                artwork[label] = artoptions[dialog].getProperty("icon")
                changemade = True
            elif (image and dialog == 2) or (not image and dialog == 0):
                # manual browse...
                image = xbmcgui.Dialog().browse(2, subheader, 'files', mask='.gif|.png|.jpg')
                if image:
                    artwork[label] = image
                    changemade = True
    return changemade, artwork


class PVRMetaData(object):

    def __init__(self):
        self.cache = simplecache.SimpleCache()
        self.tmdb = Tmdb()
        log('Initialized', type=xbmc.LOGINFO)

    def lookup_local_recording(self, title):
        """
            lookup actual recordings to get details for grouped recordings
            also grab a thumb provided by the pvr
        """
        cache = self.cache.get("recording.%s" % title)
        if cache:
            return cache
        details = dict()
        query = {'method': 'PVR.GetRecordings',
                 'params': {'properties': ['title', 'file', 'channel', 'art', 'icon', 'genre']}}
        result = jsonrpc(query)
        for item in result['recordings']:
            if title == item["title"] or title in item["file"]:

                # grab thumb from pvr
                if item.get("art"): details.update({'thumbnail': item['art'].get('thumb')})
                # ignore tvheadend thumb as it returns the channellogo
                elif item.get("icon") and "imagecache" not in item["icon"]: details.update({'thumbnail': item['icon']})

                details.update({'channel': item['channel'], 'genre': ' / '.join(item['genre'])})
                break

        self.cache.set("recording.%s" % title, details, expiration=timedelta(days=365))
        return details

    def lookup_custom_path(self, searchtitle, title):
        """
            looks up a custom directory if it contains a subdir for the title
        """

        # ToDo: Grab artists if an .artists folder exists

        details = dict()
        title_path = self.get_custom_path(searchtitle, title)
        if title_path and xbmcvfs.exists(title_path):
            # we have found a folder for the title, look for artwork
            files = xbmcvfs.listdir(title_path)[1]
            for item in files:
                if item.split('.')[0] in dict_arttypes:
                    details['art'][item.split('.')[0]] = os.path.join(title_path, item)
            details.update({'path': title_path})
        if details: log('fetch artwork from %s' % title_path)
        return details

    @staticmethod
    def lookup_local_library(title, media_type):
        """
            lookup the title in the local video db
        """
        log('look up in local databases for \'%s\'' % title)
        details = dict()

        if not media_type or media_type == "tvshow":
            query = {'method': 'VideoLibrary.GetTVShows',
                     'params': {'properties': ['art', 'file'],
                                'limits': {'start': 0, 'end': 1},
                                'filter': {"operator": "is", "field": "title", "value": title}
                                }
                     }
            result = jsonrpc(query)
            if result and len(result['tvshows']) > 0:
                details.update({'art': result['tvshows'][0].get('art', '')})
                details.update({'media_type': 'tvshow', 'path': result['tvshows'][0].get('file', '')})
                media_type = 'tvshow'

        if not details and (not media_type or media_type == "movie"):
            query = {'method': 'VideoLibrary.GetMovies',
                     'params': {'properties': ['art', 'file'],
                                'limits': {'start': 0, 'end': 1},
                                'filter': {"operator": "is", "field": "title", "value": title}
                                }
                     }
            result = jsonrpc(query)
            if result and len(result['movies']) > 0:
                details.update({'art': result['movies'][0].get('art', '')})
                details.update({'media_type': 'movie', 'path': result['movies'][0].get('file', '')})
                media_type = 'movie'

        if 'art' in details:
            for [key, value] in details['art'].items(): details['art'][key] = url_unquote(value)

        if details and ADDON.getSetting('log_results') == 'true':
            log('fetch data for \'%s\' in %s database:' % (title, media_type), pretty_print=details)
        else:
            log('no results in local databases')

        return details

    @staticmethod
    def get_custom_path(searchtitle, title):
        """
            locate custom folder on disk as pvrart location
        """
        title_path = ""
        custom_path = ADDON.getSetting("pvr_art_custom_path")
        if ADDON.getSetting("pvr_art_custom") == "true":
            dirs = xbmcvfs.listdir(custom_path)[0]

            for strictness in [1, 0.95, 0.9, 0.8]:
                for directory in dirs:
                    curpath = os.path.join(custom_path, directory)
                    for item in [title, searchtitle]:
                        match = SM(None, item, directory).ratio()
                        if match >= strictness: return curpath

            if not title_path and ADDON.getSetting("pvr_art_download") == "true":
                title_path = os.path.join(custom_path, normalize_string(title))
        return title_path

    @staticmethod
    def cleanup_title(title):
        """
            common logic to get a proper searchtitle from crappy titles provided by pvr
        """
        # split characters - split on common splitters
        splitters = ADDON.getSetting("pvr_art_splittitlechar").split("|")

        for splitchar in splitters:
            title = title.split(splitchar)[0]

        # replace common chars and words and return title
        return re.sub(ADDON.getSetting("pvr_art_replace_by_space"), ' ', title).strip()

    @staticmethod
    def pvr_proceed_lookup(title, channel, genre, recordingdetails):
        """
            perform some checks if we can proceed with the lookup
        """
        filters = list()
        channel = pure_channelname(channel)
        if not title:
            filters.append("Title is empty")

        for item in ADDON.getSetting("pvr_art_ignore_titles").split(", "):
            if item and item.lower() == title.lower():
                filters.append("Title is in list of titles to ignore")

        for item in ADDON.getSetting("pvr_art_ignore_channels").split(", "):
            if item and item.lower() == channel.lower():
                filters.append("Channel is in list of channels to ignore")

        for item in ADDON.getSetting("pvr_art_ignore_genres").split(", "):
            if genre and item and item.lower() in genre.lower():
                filters.append("Genre is in list of genres to ignore")

        if ADDON.getSetting("pvr_art_ignore_commongenre") == "true":
            # skip common genres like sports, weather, news etc.
            genre = genre.lower()
            kodi_strings = [19516, 19517, 19518, 19520, 19548, 19549, 19551,
                            19552, 19553, 19554, 19555, 19556, 19557, 19558, 19559]
            for kodi_string in kodi_strings:
                kodi_string = xbmc.getLocalizedString(kodi_string).lower()
                if (genre and (genre in kodi_string or kodi_string in genre)) or kodi_string in title:
                    filters.append("Common genres like weather/sports are set to be ignored")
        if ADDON.getSetting("pvr_art_recordings_only") == "true" and not recordingdetails:
            filters.append("PVR Artwork is enabled for recordings only")
        if filters:
            filterstr = " - ".join(filters)
            log("Filter active for title: %s - channel %s --> %s" % (title, channel, filterstr))
            return filterstr
        else:
            return ""

    @staticmethod
    def get_mediatype_from_genre(genre):
        """guess media type from genre for better matching"""
        media_type = ""
        if "movie" in genre.lower() or "film" in genre.lower():
            media_type = "movie"
        if "show" in genre.lower():
            media_type = "tvshow"
        if not media_type:

            # Kodi defined movie genres
            kodi_genres = [19500, 19507, 19508, 19602, 19603]
            for kodi_genre in kodi_genres:
                if xbmc.getLocalizedString(kodi_genre) in genre:
                    media_type = "movie"
                    break
        if not media_type:

            # Kodi defined tvshow genres
            kodi_genres = [19505, 19516, 19517, 19518, 19520, 19532, 19533, 19534, 19535, 19548, 19549,
                           19550, 19551, 19552, 19553, 19554, 19555, 19556, 19557, 19558, 19559]
            for kodi_genre in kodi_genres:
                if xbmc.getLocalizedString(kodi_genre) in genre:
                    media_type = "tvshow"
                    break
        return media_type

    @staticmethod
    def translate_string(_str):
        """
            translate the received english string for status from the various sources like tvdb, tmbd etc
        """
        status = {'continuing': LOC(32037), 'ended': LOC(32038), 'returning': LOC(32039), 'released': LOC(32040),
                  'canceled': LOC(32045)}
        if _str.split(' ')[0].lower() in status: return status[_str.split(' ')[0].lower()]
        return _str

    @staticmethod
    def calc_duration(duration):
        """
            helper to get a formatted duration
        """
        if isinstance(duration, str) and ":" in duration:
            hours, mins = duration.split(':')
            return {'Duration': duration, 'Runtime': int(hours) * 60 + int(mins)}
        else:
            hours = str(int(duration) // 60)
            _m = int(duration) % 60
            mins = str(_m) if _m > 9 else '0' + str(_m)
            return {'Duration': '%s:%s' % (hours, mins), 'Runtime': int(duration)}

    def get_tmdb_details(self, imdb_id=None, tvdb_id=None, title=None, year=None, media_type=None,
                         preftype=None, manual_select=False, ignore_cache=False):
        """
            returns details from tmdb
        """
        log('Fetch items from tmdb: ImdbId: %s, TvdbId: %s, title: %s, year: %s, '
            'mediatype: %s, preferred type: %s, manual selection: %s, ignore cache: %s' %
            (imdb_id, tvdb_id, title, year, media_type, preftype, manual_select, ignore_cache))

        result = dict()
        if imdb_id:
            result = self.tmdb.get_videodetails_by_externalid(imdb_id, "imdb_id")
        elif tvdb_id:
            result = self.tmdb.get_videodetails_by_externalid(tvdb_id, "tvdb_id")
        elif title and media_type in ["movies", "setmovies", "movie"]:
            result = self.tmdb.search_movie(title, year, manual_select=manual_select)
        elif title and media_type in ["tvshows", "tvshow"]:
            result = self.tmdb.search_tvshow(title, year, manual_select=manual_select)
        elif title:
            result = self.tmdb.search_video(title, year, preftype=preftype, manual_select=manual_select)

        if result and result.get("status"):
            result["status"] = self.translate_string(result["status"])
        if result and result.get("runtime"):
            result["runtime"] = result["runtime"] / 60
            result.update(self.calc_duration(result["runtime"]))
        return result

    def get_pvr_artwork(self, title, channel="", genre="", year="", manual_select=False, ignore_cache=False):
        """
            collect full metadata and artwork for pvr entries (MAINFUNCTION)
            parameters: title (required)
            channel: channel name (required)
            year: year or date (optional)
            genre: (optional)
            the more optional parameters are supplied, the better the search results
        """
        # try cache first
        # use cleantitle when searching cache

        searchtitle = self.cleanup_title(title.lower())
        cache_str = "pvr_artwork.%s.%s" % (searchtitle, channel.lower())
        cache = self.cache.get(cache_str)

        if cache and channel and not manual_select and not ignore_cache:
            log("fetch data from cache: %s" % cache_str)
            details = cache
            if ADDON.getSetting('log_results') == 'true':
                log('lookup for title: %s - final result:' % searchtitle, pretty_print=details)
            return details
        else:
            # no cache - start our lookup adventure
            log("no data in cache - start lookup: %s" % cache_str)

            # workaround for recordings
            recording = self.lookup_local_recording(title)
            art = ''
            if recording:
                art = recording['thumbnail']
                if not (channel and genre):
                    genre = recording["genre"]
                    channel = recording["channel"]

            details = dict({'pvrtitle': title, 'pvrchannel': channel, 'pvrgenre': genre, 'cachestr': cache_str,
                            'media_type': '', 'art': dict()})
            if art: details.update({'thumbnail': art})

            # filter genre unknown/other
            if not genre or genre.split(" / ")[0] in xbmc.getLocalizedString(19499).split(" / "):
                details.update({'genre': list()})
                genre = ""
                log("Genre is unknown, ignore....")
            else:
                details.update({'genre': genre.split(' / '), 'media_type': self.get_mediatype_from_genre(genre)})
            searchtitle = self.cleanup_title(title.lower())

            # only continue if we pass our basic checks
            excluded = self.pvr_proceed_lookup(title, channel, genre, recording)
            proceed_lookup = False if excluded else True

            if not proceed_lookup and manual_select:
                # warn user about active skip filter
                proceed_lookup = xbmcgui.Dialog().yesno(message=LOC(32027), heading=LOC(750))
            if not proceed_lookup: return

            # if manual lookup get the title from the user
            if manual_select:
                searchtitle = xbmcgui.Dialog().input(xbmc.getLocalizedString(16017), searchtitle,
                                                     type=xbmcgui.INPUT_ALPHANUM)
                if not searchtitle: return

            # if manual lookup and no mediatype, ask the user
            if manual_select and not details["media_type"]:
                choice = xbmcgui.Dialog().yesnocustom(LOC(32022), LOC(32041) % searchtitle, LOC(32016),
                                                      nolabel=LOC(32043), yeslabel=LOC(32042))
                if choice == 0: details["media_type"] = "tvshow"
                elif choice == 1: details["media_type"] = "movie"

            # append thumb from recordingdetails
            if recording and recording.get("thumbnail"): details["art"]["thumb"] = recording["thumbnail"]

            # lookup movie/tv library
            details = extend_dict(details, self.lookup_local_library(searchtitle, details["media_type"]))

            # lookup custom path
            details = extend_dict(details, self.lookup_custom_path(searchtitle, title))

            # do TMDB scraping if enabled and no arts in previous lookups
            if ADDON.getSetting("use_tmdb").lower() == "true" and not details.get('art', False) \
                    and ADDON.getSetting('tmdb_apikey'):

                log("scraping metadata from TMDB for title: %s (media type: %s)" % (searchtitle, details["media_type"]))
                tmdb_result = self.get_tmdb_details(title=searchtitle, preftype=details["media_type"], year=year,
                                                    manual_select=manual_select, ignore_cache=manual_select)
                if tmdb_result:
                    details["media_type"] = tmdb_result["media_type"]
                    details = extend_dict(details, tmdb_result)
                elif ignore_cache:
                    xbmcgui.Dialog().notification(LOC(32001), LOC(32021), xbmcgui.NOTIFICATION_WARNING)

                thumb = ''
                if 'thumbnail' in details:
                    thumb = details["thumbnail"]
                else:
                    for item in details['art']:
                        if 'landscape' in item: thumb = item["landscape"]
                        elif 'fanart' in item: thumb = item["fanart"]
                        elif 'poster' in item: thumb = item["poster"]
                        if thumb: break
                if thumb:
                    details.update({'thumbnail': thumb})
                    details["art"].append({'thumb': thumb})

                # download artwork to custom folder
                if ADDON.getSetting("pvr_art_download").lower() == "true":
                    details.update({'path': self.get_custom_path(searchtitle, title)})
                    details["art"] = download_artwork(details['path'], details["art"])

            if ADDON.getSetting('log_results') == 'true':
                log('lookup for title: %s - final result:' % searchtitle, pretty_print=details)

        # always store result in cache
        log("store data in cache - %s " % cache_str)
        self.cache.set(cache_str, details, expiration=timedelta(days=365))
        return details

    # Main entry from context menu call
    # Do not remove

    def pvr_artwork_options(self, title, channel, genre, year):
        """
            show options for pvr artwork
        """

        # Refresh item (auto lookup), Refresh item (manual lookup), Choose art
        options = list([LOC(32028), LOC(32029), LOC(32036)])
        channel = pure_channelname(channel)

        ignorechannels = split_addonsetting('pvr_art_ignore_channels', ', ')
        ignoretitles = split_addonsetting('pvr_art_ignore_titles', ', ')

        if channel in ignorechannels:
            options.append(LOC(32030))  # Remove channel from ignore list
        else:
            options.append(LOC(32031))  # Add channel to ignore list
        if title in ignoretitles:
            options.append(LOC(32032))  # Remove title from ignore list
        else:
            options.append(LOC(32033))  # Add title to ignore list

        options.append(LOC(32034))  # Open addon settings

        dialog = xbmcgui.Dialog().select(LOC(32035), options)
        if dialog == 0:
            # Refresh item (auto lookup)
            #
            # FOR TESTING CACHE MECHANISM SET 'IGNORE_CACHE' TO FALSE !!!
            #
            log('Auto lookup for title: %s (%s), channel: %s, genre: %s' % (title, year, channel, genre))
            self.get_pvr_artwork(title=title, channel=channel, genre=genre, year=year,
                                 ignore_cache=True, manual_select=False)
        elif dialog == 1:
            # Refresh item (manual lookup)
            log('Manual lookup for title: %s (%s), channel: %s, genre: %s' % (title, year, channel, genre))
            self.get_pvr_artwork(title=title, channel=channel, genre=genre, year=year,
                                 ignore_cache=True, manual_select=True)
        elif dialog == 2:
            # Choose art
            self.manual_set_pvr_artwork(title, channel, genre)
        elif dialog == 3:
            # Add/remove channel to ignore list
            if channel in ignorechannels:
                ignorechannels.remove(channel)
            else:
                ignorechannels.append(channel)
            ADDON.setSetting("pvr_art_ignore_channels", ', '.join(ignorechannels))
        elif dialog == 4:
            # Add/remove title to ignore list
            if title in ignoretitles:
                ignoretitles.remove(title)
            else:
                ignoretitles.append(title)
            ADDON.setSetting("pvr_art_ignore_titles", ', '.join(ignoretitles))
        elif dialog == 5:
            # Open addon settings
            xbmc.executebuiltin("Addon.OpenSettings(%s)" % ADDON_ID)

    def manual_set_pvr_artwork(self, title, channel, genre):
        """manual override artwork options"""

        details = self.get_pvr_artwork(title=title, channel=channel, genre=genre)
        cache_str = details["cachestr"]

        # show dialogselect with all artwork option
        changemade, artwork = manual_set_artwork(details["art"])
        if changemade:
            details["art"] = artwork
            # save results in cache
            self.cache.set(cache_str, details, expiration=timedelta(days=365))