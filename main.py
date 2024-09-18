from lib.tools import *
from lib.pvrmetadata import PVRMetaData

Pmd = PVRMetaData()

content_types = dict({'MyPVRChannels.xml': 'ListItem', 'MyPVRGuide.xml': 'ListItem', 'DialogPVRInfo.xml': 'ListItem',
                      'MyPVRRecordings.xml': 'Container(50).ListItem', 'MyPVRTimers.xml': 'Container(50).ListItem',
                      'MyPVRSearch.xml': 'Container(50).ListItem', 'DialogPVRChannelsOSD.xml': 'Container(11).ListItem',
                      'DialogPVRChannelGuide.xml': 'Container(11).ListItem'})

win = xbmcgui.Window(10000)
prefix = 'PVR.Artwork'

def pvrartwork(t, c):

    if xbmc.getCondVisibility('Container(%s).Scrolling') % xbmcgui.getCurrentWindowId() or \
            win.getProperty('%s.Lookup' % prefix) == 'busy':
        xbmc.sleep(500)
        xbmc.log('Artwork module is busy or scrolling is active, return')
        return t, c

    # check if Live TV or PVR related window is active

    label = 'VideoPlayer' if xbmc.getCondVisibility('VideoPlayer.Content(livetv)') else None
    for pvr_content in content_types:
        if xbmc.getCondVisibility('Window.IsActive(%s)' % pvr_content):
            label = content_types.get(pvr_content, None)
            break

    # if no pvr related label there, clear properties and return
    if label is None:
        if win.getProperty('%s.present' % prefix) == 'true': Pmd.clear_properties(prefix)
        return '', ''

    title = xbmc.getInfoLabel('%s.Title' % label)
    if not title: title = xbmc.getInfoLabel('%s.Label' % label)

    channel = xbmc.getInfoLabel('%s.ChannelName' % label)
    if not channel: channel = xbmc.getInfoLabel('VideoPlayer.ChannelName')

    genre = xbmc.getInfoLabel('%s.Genre' % label)
    year = xbmc.getInfoLabel('%s.Year' % label)

    if not (title or channel): return '', ''

    if (t != title or c != channel) and win.getProperty('%s.Lookup' % prefix) != 'busy':
        try:
            Pmd.get_pvr_artwork(prefix, title, channel, genre, year, manual_select=False, ignore_cache=False)
        except Exception:
            win.clearProperty('%s.Lookup' % prefix)
            xbmc.log('PVR Artwork module error', xbmcgui.NOTIFICATION_ERROR)

    return title, channel


if __name__ == '__main__':
    t = ''
    c = ''
    monitor = xbmc.Monitor()
    xbmc.log('PVR Artwork module wrapper started', level=xbmc.LOGINFO)

    while not monitor.abortRequested():
        if monitor.waitForAbort(1): break
        if xbmc.getCondVisibility('Skin.HasSetting(Skin_enablePvrArtwork)'):
            t, c = pvrartwork(t, c)

    Pmd.clear_properties(prefix)
    xbmc.log('PVR Artwork module wrapper finished', level=xbmc.LOGINFO)
