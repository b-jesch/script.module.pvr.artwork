## PVR artwork module ##

The addon offers several ways to generate content. Generated content is cached for 90, 180 or 360 days. The search process is as follows:

- Previously cached content is read out. The title, year of release and media type (film/series) of a series or film serve as criteria.
- the series/movies available in the databases are checked for hits with the title to be searched and the information (artwork, meta data) is provided.
- previously defined folders are checked for hits with the titles to be searched and the artwork available in these folders is provided. This process cannot provide metadata (genre, release date, etc.).
- the final step involves searching for a series/movie on TMDB.org. This requires a valid API key in addition to an online connection. Artwork available at TMDB as well as metadata will be provided.

The functions of the module should be called periodically from a service when the following PVR windows are displayed:

- MyPVRChannels.xml
- MyPVRGuide.xml
- MyPVRRecordings.xml
- MyPVRTimers.xml
- MyPVRSearch.xml

Unless information provided by ListItems changes, metadata and artwork do not need to be updated.

A complete implementation and function calls can be found here:
## Context Menu Script ##
[https://github.com/b-jesch/skin.estuary.modv2/blob/master/scripts/context_menu_pvr.py](https://github.com/b-jesch/skin.estuary.modv2/blob/master/scripts/services.py)

This script should be defined as a context item within the addon.xml of a skin.
```

"""
    Contextmenu for Pvr art applied from script.skinhelper.service
    thanks to Marcel van der Veldt and contributors
"""

import xbmc
import xbmcgui
import sys

try:
    from pvrmetadata import PVRMetaData
except ImportError:
    sys.exit()

if __name__ == '__main__':

    win = xbmcgui.Window(10000)
    win.setProperty("PVR.Artwork.ManualLookup", "busy")
    title = xbmc.getInfoLabel("ListItem.Title")
    if not title:
        title = xbmc.getInfoLabel("ListItem.Label")

    channel = xbmc.getInfoLabel("ListItem.ChannelName")
    genre = xbmc.getInfoLabel("ListItem.Genre")
    year = xbmc.getInfoLabel("ListItem.Year")

    pmd = PVRMetaData()
    pmd.pvr_artwork_options(title, channel, genre, year)

    win.setProperty("PVR.Artwork.ManualLookup", "changed")
    del win
```

## Service Script ##
[https://github.com/b-jesch/skin.estuary.modv2/blob/master/scripts/services.py](https://github.com/b-jesch/skin.estuary.modv2/blob/master/scripts/services.py)

An example for a service script. All properties are stored within the Home Window (Window ID 10000) with following syntax:

### Labels ###
- `PVR.Artwork.ListItem.genre`
- `PVR.Artwork.ListItem.director`
- `PVR.Artwork.ListItem.castandrole`

and more (see pvrmetadata.py: line 20)

### Artwork ###
- `PVR.Artwork.fanart`
- `PVR.Artwork.poster`
- `PVR.Artwork.fanart1`
- `PVR.Artwork.fanart2`

and soon

```
import xbmc
import xbmcgui

pam = False
try:
    from pvrmetadata import PVRMetaData
    pmd = PVRMetaData()
    pam = True
except ImportError:
    xbmc.log('PVR artwork module not available', xbmc.LOGWARNING)

# PVR artwork

content_types = dict({'MyPVRChannels.xml': 'channels', 'MyPVRGuide.xml': 'tvguide', 'DialogPVRInfo.xml': 'info',
                      'MyPVRRecordings.xml': 'recordings', 'MyPVRTimers.xml': 'timers', 'MyPVRSearch.xml': 'search'})

win = xbmcgui.Window(10000)


def pvrartwork(current_item):

    prefix = 'PVR.Artwork'
    current_content = None

    if xbmc.getCondVisibility('Container(%s).Scrolling') % xbmcgui.getCurrentWindowId() or \
            win.getProperty('%s.Lookup' % prefix) == 'busy':
        xbmc.sleep(500)
        xbmc.log('Artwork module is busy or scrolling is active, return')
        return current_item

    # check if Live TV or PVR related window is active

    for pvr_content in content_types:
        if xbmc.getCondVisibility('Window.IsActive(%s)' % pvr_content):
            current_content = content_types.get(pvr_content, None)
            break

    if current_content is None and xbmc.getCondVisibility('VideoPlayer.Content(LiveTV)'): current_content = 'livetv'

    # if no pvr related window there, clear properties and return
    if current_content is None:
        if win.getProperty('%s.present' % prefix) == 'true': pmd.clear_properties(prefix)
        return ''

    label = 'VideoPlayer' if current_content == 'livetv' else 'ListItem'
    title = xbmc.getInfoLabel('%s.Title' % label)
    if label == 'ListItem' and not title: title = xbmc.getInfoLabel('%s.Label' % label)
    channel = xbmc.getInfoLabel('%s.ChannelName' % label)
    genre = xbmc.getInfoLabel('%s.Genre' % label)
    year = xbmc.getInfoLabel('%s.Year' % label)

    if not (title or channel): return ''

    if current_item != '%s-%s' % (title, channel) and win.getProperty('%s.Lookup' % prefix) != 'busy':
        pmd.get_pvr_artwork(prefix, title, channel, genre, year, manual_select=False, ignore_cache=False)

    return '%s-%s' % (title, channel)

if __name__ == '__main__':

    # properties for pvrartwork
    current_item = ''

    monitor = xbmc.Monitor()
    xbmc.log('Estuary MOD V2 Matrix Service handler started', level=xbmc.LOGINFO)

    while not monitor.abortRequested():
        if monitor.waitForAbort(0.5): break

        # call services
        # PVR artwork
        if pam and xbmc.getCondVisibility('Skin.HasSetting(Skin_enablePvrArtwork)'):
            current_item = pvrartwork(current_item)

    xbmc.log('Estuary MOD V2 Matrix Service handler finished')
```
