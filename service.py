from lib.tools import *
import sys
from urllib.parse import parse_qsl

try:
    from lib.pvrmetadata import PVRMetaData
except ImportError:
    sys.exit()

if len(sys.argv) > 1:
    if sys.argv[1] == 'clear_db':

        artwork = ADDON.getSetting('pvr_art_custom_path')
        yesno = xbmcgui.Dialog().yesno(LOC(32050), LOC(32059) % artwork)
        if yesno:

            # clear cache

            import sqlite3
            sc = xbmcvfs.translatePath(xbmcaddon.Addon(id='script.module.simplecache').getAddonInfo('profile'))
            dbpath = os.path.join(sc, 'simplecache.db')
            connection = sqlite3.connect(dbpath, timeout=30, isolation_level=None)
            try:
                connection.execute('DELETE FROM simplecache WHERE id LIKE ?', (DB_PREFIX + '%',))
                connection.commit()
                connection.close()
                xbmcgui.Dialog().notification(LOC(32001), LOC(32051), xbmcgui.NOTIFICATION_INFO)
            except sqlite3.Error as e:
                log(str(e.args[0]), xbmc.LOGERROR)
            finally:
                del connection

            # remove artwork files and folders

            dirs, files = xbmcvfs.listdir(artwork)
            if len(dirs) > 0:
                count = rmdirs(artwork, force=True)
                xbmcgui.Dialog().notification(LOC(32001), LOC(32070) % count, xbmcgui.NOTIFICATION_INFO)
            else:
                xbmcgui.Dialog().notification(LOC(32001), LOC(32072), xbmcgui.NOTIFICATION_WARNING)

    elif sys.argv[1] == 'call_contextmenu':
        title = xbmc.getInfoLabel("ListItem.Title")
        if not title:
            title = xbmc.getInfoLabel("ListItem.Label")

        channel = xbmc.getInfoLabel("ListItem.ChannelName")
        genre = xbmc.getInfoLabel("ListItem.Genre")
        year = xbmc.getInfoLabel("ListItem.Year")

        pmd = PVRMetaData()
        pmd.pvr_artwork_options('PVR.Artwork', title, channel, genre, year)

    elif sys.argv[1] == 'get_artwork':
        params = dict(parse_qsl(sys.argv[2]))
        pmd = PVRMetaData()
        try:
            pmd.get_pvr_artwork(params['prefix'], params['title'], params['genre'], params['channel'],
                                manual_select=False, ignore_cache=False)
        except KeyError as e:
            log('An error has occurred: %s' % str(e), xbmc.LOGERROR)

    elif sys.argv[1] == 'clear_artwork':
        params = dict(parse_qsl(sys.argv[2]))
        pmd = PVRMetaData()
        try:
            pmd.clear_properties(params['prefix'])
        except KeyError as e:
            log('An error has occurred: %s' % str(e), xbmc.LOGERROR)

    else:
        log('unknown command parameter: %s' % sys.argv[1], xbmc.LOGWARNING)
else:
    log('no command parameter provided', xbmc.LOGWARNING)
