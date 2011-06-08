# -*- coding: utf-8 -*- 
import re


PLUGIN_TITLE = L('Title')
PLUGIN_PREFIX = "/video/istikana"


ISTIKANA_NAMESPACE = {'thr':'http://purl.org/syndication/thread/1.0' , 'openSearch':'http://a9.com/-/spec/opensearch/1.1/' ,'media':'http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom'}


NAME = L('Title')

# Default artwork and icon(s)
PLUGIN_ARTWORK = 'art-default.jpg'
PLUGIN_ICON_DEFAULT = 'icon-default.png'
PLUGIN_ICON_PREFS = 'icon-prefs.png'
PLUGIN_ICON_NEXT = 'icon-next.png'
PLUGIN_ICON_PREVIOUS = 'icon-previous.png'



# Lets Disable the Arabic feed for now. Plex has an issue displaying Arabic content.
# The english feed will do just fine.
URLS = [
  #['ar', 'http://www.istikana.com/%s/atom/tv_shows', '%s/%%s', '%s/%%s'],
  ['en', 'http://www.istikana.com/%s/atom/tv_shows', '%s/%%s', '%s/%%s']
]


# Some constants for the RTMP streamng.
NET_CONNECTION_URL= 'rtmp://videos.istikana.com/cfx/st'
CLIP_URL= 'mp4:videos/200/%s/%s'


####################################################################################################

def Start():

    ## make this plugin show up in the 'Video' section
    ## in Plex. The L() function pulls the string out of the strings
    ## file in the Contents/Strings/ folder in the bundle
    ## see also:
    ##  http://dev.plexapp.com/docs/mod_Plugin.html
    ##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ## set some defaults so that you don't have to
    ## pass these parameters to these object types
    ## every single time
    ## see also:
    ##  http://dev.plexapp.com/docs/Objects.html
    MediaContainer.title1 = PLUGIN_TITLE
    MediaContainer.viewGroup = "List"
    MediaContainer.art = R(PLUGIN_ARTWORK)
    DirectoryItem.thumb = R(PLUGIN_ICON_DEFAULT)
    VideoItem.thumb = R(PLUGIN_ICON_DEFAULT)
    
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10'
		
		
		
def MainMenu():
    dir = MediaContainer(noCache=True)
    
    xml = RSS.FeedFromURL(getURLs()[0])
    
    next_page = GetPage(xml['feed']['links'], 'next')
    previous_page = GetPage(xml['feed']['links'], 'previous')

    
    for video in xml.entries:
        title = video['title']        
        thumb = video['media_thumbnail'][0]["url"]
        episodes_url = video['links'][1]['href']
        
        dir.Append(Function(DirectoryItem(Episodes, title=title, thumb=Function(GetThumb, url=thumb)), title=title, episodes_url=episodes_url ))
    
    if(next_page):  
        dir.Append(Function(DirectoryItem(Shows, title="Next Page", thumb=R(PLUGIN_ICON_NEXT)), show_url= next_page['href']))
    
    if(previous_page):  
        dir.Append(Function(DirectoryItem(Shows, title="Previous Page", thumb=R(PLUGIN_ICON_PREVIOUS)), show_url= previous_page['href']))

    return dir


# This is a replica for the MainMenu, its working, but not the smartest way to do things.
# We need this function for a callback for "next page", "previous page"
# 
def Shows(sender, show_url):
    dir = MediaContainer(title2=PLUGIN_TITLE, viewGroup='List')
    
    xml = RSS.FeedFromURL(show_url)
    
    next_page = GetPage(xml['feed']['links'], 'next')
    previous_page = GetPage(xml['feed']['links'], 'previous')
    
    for video in xml.entries:
        title = video['title']        
        thumb = video['media_thumbnail'][0]["url"]
        episodes_url = video['links'][1]['href']
        
        dir.Append(Function(DirectoryItem(Episodes, title=title, thumb=Function(GetThumb, url=thumb)), title=title, episodes_url=episodes_url ))

    if(next_page):  
        dir.Append(Function(DirectoryItem(Shows, title="Next Page", thumb=R(PLUGIN_ICON_NEXT)), show_url= next_page['href']))
    
    if(previous_page):  
        dir.Append(Function(DirectoryItem(Shows, title="Previous Page", thumb=R(PLUGIN_ICON_PREVIOUS)), show_url= previous_page['href']))
            
    return dir



def Episodes(sender, title, episodes_url):
    dir = MediaContainer(title2=title, viewGroup='List')
    
    # Extract the Show name from the URL
    show_name = GetShowName(episodes_url)    
    
    # Fetch and Parse the XML
    xml = RSS.FeedFromURL(episodes_url)
    
    for video in xml.entries:
        title = video['title']        
        thumb = video['media_thumbnail'][1]['url']
        
        html_url = video['link']
        episode_name = GetEpisodeName(html_url)
        
        # Opening the videopage at this point to find the info is going to take too much time, as we need to open pages for all the
        # videos in the list we're buidling here.
        # Instead we postpone those steps until the moment a user selects a video. For this we add an extra function that's going to
        # be called at the moment a user selects a video.
        dir.Append(Function(WebVideoItem(PlayVideo, title=title, summary="", thumb=Function(GetThumb, url=thumb)), show_name=show_name, episode_name=episode_name))

    return dir




####################################################################################################

def getURLs():
    for language, base_url, show_url, episode_url in URLS:
        if Prefs['language'] == language:
            return [(base_url % language)]

def GetThumb(url):
    try:
        data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
        return DataObject(data, 'image/jpeg')
    except:
        pass
    return Redirect(R(PLUGIN_ICON_DEFAULT))


# Get The show name given the feed url
# URL: http://www.istikana.com/en/atom/tv_shows/sanshiro
# output: "sanshiro"
#
def GetShowName(url):
    return GetLastPath(url)


# Get The show name given the feed url
# URL: http://www.istikana.com/en/episodes/sanshiro-1
# output: "sanshiro-1"
#
def GetEpisodeName(url):
    return GetLastPath(url)



# Get the last path from a url
# URL: http://www.istikana.com/en/atom/tv_shows/ahlan-nabil-and-hisham-2
# We need to extract "ahlan-nabil-and-hisham-2"
#
def GetLastPath(url):
    # Split the url using "/" and find the episode name
    data = url.split("/")
    return data.pop()


def PlayVideo(sender, show_name, episode_name):
    clip = (CLIP_URL % (show_name,episode_name))
    return Redirect(RTMPVideoItem(NET_CONNECTION_URL, clip))


# Get a pagnation options from the pagination links
# 
#
def GetPage(links, page):
    for link in links:
        if page == link['rel']:
            return link
        
