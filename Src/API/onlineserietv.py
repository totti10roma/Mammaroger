from Src.Utilities.info import get_info_imdb, is_movie, get_info_tmdb
from bs4 import BeautifulSoup,SoupStrainer
import Src.Utilities.config as config
from fake_headers import Headers  
from Src.Utilities.loadenv import load_env  
import json, random
import re
from Src.Utilities.eval import eval_solver
import urllib.parse
from Src.API.extractors.maxstream import maxstream
from Src.API.extractors.uprot import bypass_uprot
OST_DOMAIN = config.OST_DOMAIN
OST_PROXY = config.OST_PROXY
env_vars = load_env()
proxies = {}
random_headers = Headers()
import logging
from Src.Utilities.config import setup_logging
level = config.LEVEL
logger = setup_logging(level)

if OST_PROXY == "1":
    PROXY_CREDENTIALS = env_vars.get('PROXY_CREDENTIALS')
    proxy_list = json.loads(PROXY_CREDENTIALS)
    proxy = random.choice(proxy_list)
    if proxy == "":
        proxies = {}
    else:
        proxies = {
            "http": proxy,
            "https": proxy
        }   
OST_ForwardProxy = config.OST_ForwardProxy
if OST_ForwardProxy == "1":
    ForwardProxy = env_vars.get('ForwardProxy')
else:
    ForwardProxy = ""
Name = config.Name
Icon = config.Icon

async def search(showname,date,client,ismovie,episode,season):
    headers = random_headers.generate()
    headers['Referer'] = f'{OST_DOMAIN}/'
    cookies = {
    'player_opt': 'fx',
    }
    params = {
    's': showname,
    'action': 'searchwp_live_search',
    'swpengine': 'default',
    'swpquery': showname,
    'origin_id': '50141',
    'searchwp_live_search_client_nonce': 'undefined',
    }
    response = await client.get(ForwardProxy + f"{OST_DOMAIN}/wp-admin/admin-ajax.php?s={urllib.parse.quote(showname)}&action=searchwp_live_search&swpengine=default&swpquery={urllib.parse.quote(showname)}&origin_id=50141&searchwp_live_search_client_nonce=undefined", headers=headers, cookies=cookies, impersonate = "chrome", proxies = proxies)
    if response.status_code != 200:
        logger.info("IP Blocked by OnlineserieTV",response)
    soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('a'))
    a_tags_with_href = soup.find_all("a", href=True)
    for a_tag in a_tags_with_href:
        href = a_tag.get("href")
        if ismovie == 1:
            if "film" in href:
                response = await client.get(ForwardProxy + href, headers=headers, impersonate = "chrome", proxies = proxies)
                if response.status_code != 200:
                    logger.info("IP Blocked by OnlineserieTV",response)
                year_match = re.search(r'Anno: <i>(\d{4})</i>', response.text)
                year = year_match.group(1) if year_match else None
                if year == date:
                    pattern = r'https://uprot\.net/msf/[^\s"<>]+'
                    match = re.search(pattern, response.text)
                    if match:
                        name = a_tag.text.replace("\t","").replace("\n","")
                        maxstream_link = match.group()
                        return maxstream_link,name
                    else:
                        logger.info("No Maxstream link found.")
            else:
                continue
        elif ismovie == 0:
            if "serietv" in href:
                response = await client.get(ForwardProxy + href, headers=headers, impersonate = "chrome", proxies = proxies)
                if response.status_code != 200:
                    logger.info("IP Blocked by OnlineserieTV",response)
                year_match = re.search(r'Anno: <i>(\d{4})</i>', response.text)
                year = year_match.group(1) if year_match else None
                if year == date:
                    season = season.zfill(2)
                    episode = episode.zfill(2)
                    pattern = rf'{season}x{episode}.*?<a href=[\'"](https://uprot\.net/msf/[^\'"]+)'
                    match = re.search(pattern, response.text, re.DOTALL)
                    if not match:
                        pattern = rf'0{episode}.*?<a href=[\'"](https://uprot\.net/msf/[^\'"]+)'
                        match = re.search(pattern, response.text, re.DOTALL)
                    if match:
                        name = a_tag.text.replace("\t","").replace("\n","")
                        maxstream_link = match.group(1)
                        return maxstream_link,name
                    
                else:
                        logger.info("No maxstream link found.")
            else:
                continue 
    return None,None
async def get_maxstream(uprot_link,streams,language,client):
    maxstream_link = await bypass_uprot(client,uprot_link)
    if  maxstream_link:
        streams = await maxstream(maxstream_link,client,streams,'OnlineSerieTV',language,proxies,ForwardProxy)
    else:
        if  maxstream_link == False:
            return streams 
        else:
            streams['streams'].append({'name': f"{Name}",'title': f'{Icon}OnlineSerieTV\n▶️ Please do the captcha at /uprot in order to be able to play this content! \n Remember to refresh the sources!\nIf you recently did the captcha then dont worry, just refresh the sources', 'url': 'https://github.com/UrloMythus/MammaMia', 'behaviorHints': { 'bingeGroup': 'cb01'}})

    return streams

async def onlineserietv(streams,id,client):
    try:
        general = await is_movie(id)
        ismovie = general[0]
        clean_id = general[1]
        if ismovie == 0:
            season = general[2]
            episode = general[3]
        elif ismovie == 1:
            season = None
            episode = None
        type = "Onlineserietv"
        if "tt" in id:
                showname,date = await get_info_imdb(clean_id,ismovie,type,client)
        else:
            showname,date = get_info_tmdb(clean_id,ismovie,type)
        showname = showname.replace("'"," ").split("-")[0]
        uprot_link,name = await search(showname,date,client,ismovie,episode,season)
        if uprot_link != None:
            streams = await get_maxstream(uprot_link,streams,'',client)
        return streams
    except Exception as e:
        logger.info("MammaMia: Onlineserietv Failed")
        logger.info(e)
        return streams
    

async def test_animeworld():
    from curl_cffi.requests import AsyncSession
    async with AsyncSession() as client:
        test_id = "tt0120363"  # This is an example ID format
        results = await onlineserietv({'streams': []},test_id, client)
        print(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_animeworld())

    # Guru Guru tt0330592  Uomo tigre tt0206516
    #python3 -m Src.API.onlineserietv
