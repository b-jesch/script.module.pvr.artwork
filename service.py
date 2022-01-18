from lib.tools import *
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os


def rmdirs(folder, count, force=True):
    force = force
    dirs, files = xbmcvfs.listdir(folder)
    for file in files: xbmcvfs.delete(os.path.join(folder, file))
    for dir in dirs:
        rmdirs(os.path.join(folder, dir), count, force=force)
        if xbmcvfs.rmdir(os.path.join(folder, dir), force=force): count += 1
    return count


if len(sys.argv) > 1:
    if sys.argv[1] == 'clear_db':
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

    elif sys.argv[1] == 'clear_local_artwork':
        artwork = ADDON.getSetting('pvr_art_custom_path')
        yesno = xbmcgui.Dialog().yesno(LOC(32050), LOC(32059) % artwork)
        if yesno:
            count = rmdirs(artwork, 0, force=True)
            xbmcgui.Dialog().notification(LOC(32001), LOC(32070) % count, xbmcgui.NOTIFICATION_INFO)
    else:
        xbmc.log('unknown command parameter: %s' % sys.argv[1], xbmc.LOGWARNING)
else:
    xbmc.log('no command parameter provided', xbmc.LOGWARNING)

