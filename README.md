## PVR artwork module ##

The addon offers several ways to generate content. Generated content is cached for 365 days. The search process is as follows:

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

and more (see labels below)

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

content_types = dict({'MyPVRChannels.xml': 'channels', 'MyPVRGuide.xml': 'channels',
                      'MyPVRRecordings.xml': 'recordings', 'MyPVRTimers.xml': 'timers', 'MyPVRSearch.xml': 'search'})

labels = list(['director', 'writer', 'genre', 'country', 'studio', 'premiered', 'mpaa', 'status',
               'rating', 'castandrole', description])

win = xbmcgui.Window(10000)


def clear_properties(prefix):

    for item in pmd.dict_arttypes:
        win.clearProperty('%s.%s' % (prefix, item))
        for i in range(1, 6): win.clearProperty('%s.fanart%s' % (prefix, i))

    for label in labels: win.clearProperty('%s.ListItem.%s' % (prefix, label))

    win.clearProperty('PVR.Artwork.present')
    xbmc.log('Properties of %s cleared' % prefix)


def set_properties(prefix, artwork):

    # set artwork properties
    for item in artwork:
        if item in pmd.dict_arttypes: win.setProperty('%s.%s' % (prefix, item), artwork[item])

    # Lookup for fanarts/posters list
    fanarts = artwork.get('fanarts', False)
    posters = artwork.get('posters', False)
    cf = 0
    if fanarts:
        for cf, fanart in enumerate(fanarts):
            if cf > 5: break
            win.setProperty('%s.fanart%s' % (prefix, str(cf + 1)), fanart)
        cf += 1
    if posters and cf < 2:
        for count, fanart in enumerate(posters):
            if count > 5: break
            win.setProperty('%s.fanart%s' % (prefix, str(cf + count + 1)), fanart)

    win.setProperty('%s.present' % prefix, 'true')


def set_labels(prefix, data):
    # set PVR related list items
    for label in labels:
        if data.get(label, False) and data[label]:
            lvalue = str(data[label])
            if isinstance(data[label], list): lvalue = ', '.join(data[label])
            win.setProperty('%s.ListItem.%s' % (prefix, label), lvalue)


def pvrartwork(current_item):

    if xbmc.getCondVisibility('Container(%s).Scrolling') % xbmcgui.getCurrentWindowId() or \
            win.getProperty('PVR.Artwork.ManualLookup') == 'busy':
        xbmc.sleep(500)
        return current_item

    current_content = None

    # check if PVR related window is active
    for pvr_content in content_types:
        if xbmc.getCondVisibility('Window.IsActive(%s)' % pvr_content):
            current_content = content_types.get(pvr_content, None)
            break

    # if no pvr related window there, clear properties and return
    if not current_content:
        if win.getProperty('PVR.Artwork.present') == 'true': clear_properties('PVR.Artwork')
        return current_item

    title = xbmc.getInfoLabel("ListItem.Title")
    if not title:
        title = xbmc.getInfoLabel("ListItem.Label")

    channel = xbmc.getInfoLabel('ListItem.ChannelName')
    genre = xbmc.getInfoLabel('ListItem.Genre')
    year = xbmc.getInfoLabel('ListItem.Year')

    if current_item != '%s-%s' % (title, channel) or win.getProperty('PVR.Artwork.ManualLookup') == 'changed':
        win.setProperty("PVR.Artwork.ManualLookup", "busy")
        clear_properties('PVR.Artwork')

        details = pmd.get_pvr_artwork(title, channel, genre, year, manual_select=False, ignore_cache=False)
        if details is not None:
            if details.get('art', False): set_properties('PVR.Artwork', details['art'])
            set_labels('PVR.Artwork', details)

    win.clearProperty("PVR.Artwork.ManualLookup")
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
