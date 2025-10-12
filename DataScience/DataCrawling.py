from bs4 import BeautifulSoup
import cloudscraper, random, time, json, os, requests
import argparse

def get_html_pass_cloudflare(
        url: str, 
        state_file: str = 'cookies.json',
        domain_name = 'https://batdongsan.com.vn/') -> str:
    '''
    Function to get html document text --> Return: html text
    '''
    
    if not url.startswith('http'):
        return None 
    
    # list of user-agent that mimics the behaviors of real users
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    # create headers which simulate the real header, randomly using the user-agents created
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-platform': '"macOS"',
        'User-Agent': random.choice(user_agents),
        'Referer': domain_name,
        'Origin': domain_name
    }
    scraper = cloudscraper.create_scraper()

    # Load cookies
    if state_file and os.path.exists(state_file):
        with open(state_file, "r") as f:
            cookies = json.load(f)
            scraper.cookies.update(cookies)
    
    
    # Try up to 3 times if response is not accepted
    for attempt in range(3):
        try:
            time.sleep(random.uniform(1,3))

            response = scraper.get(url, headers = headers, timeout = random.randint(100,300))

            # save cookies
            if state_file:
                with open(state_file, "w") as f:
                    json.dump(requests.utils.dict_from_cookiejar(scraper.cookies), f)
        
            # Check response status
            if response.status_code in (429, 503) or "just a moment" in response.text.lower():
                # Try to use other user-agent
                headers['User-Agent'] = random.choice(user_agents)
                time.sleep(random.uniform(2,5))
                continue
            
            elif response.status_code == 200:
                html_text = response.text
                return html_text
            
            elif attempt == 2:
                print("[|X| FAIL] Cloudflare block this request")
                return None

        except Exception as e:
            print("[!!!| EXCEPTION] Exception : {}".format(e))
            return None

def parse_html(html_text):
    '''
    This function works for parsing http document
    '''
    from bs4 import BeautifulSoup
    return BeautifulSoup(html_text, 'lxml')

def get_title(html_parse: BeautifulSoup) -> list:
    '''
    Function gets the title of the articles after parsing to BeautifulSoup object
    --> Return : List of title
    '''
    return [html_parse.title.text]

def get_publisher(html_parse: BeautifulSoup) -> list:
    '''
    Function gets the publisher, or list of publisher of the document
    Publisher is a person or an organization publishing the article, not the author
    --> Return : List of publisher
    '''
    selector = '#__next main > div.ArticlePageTemplate_articlePageContainer__wcRoZ.container > div:nth-child(2) > div > div > div > div.AuthorInfo_authorName__m9KD3 > a'
    publisher_ls = html_parse.select(selector)
    if len(publisher_ls):
        return [publisher.text for publisher in publisher_ls]
    return None

def get_latest_update(html_parse: BeautifulSoup) -> list:
    '''
    Function gets the latest update time
    --> Return: list of update time
    '''
    selector = '#__next main > div.ArticlePageTemplate_articlePageContainer__wcRoZ.container > div:nth-child(2) > div > div > div > div.AuthorInfo_postDate__UTKIr'
    update_time_ls = html_parse.select(selector)

    if len(update_time_ls):
        return [update_time.text for update_time in update_time_ls]
    return None

def get_content(html_parse: BeautifulSoup) -> dict:
    '''
    Function gets the article's content
    --> Return: dict: {
        "content"       : str,
        "author"        : str,
        "source"        : str,
        "publish time"  : str,
        "link source"   : str
    }
    '''
    selector = '#__next main > div.ArticlePageTemplate_articlePageContainer__wcRoZ.container > div:nth-child(4) > div.col-xl-8.col-lg-8.col-md-12.col-12 > article > div:nth-child(1) > *'
    content_list = html_parse.select(selector)
    if len(content_list):
        full_content = ''
        accept_tag = ['div', 'h1', 'h2', 'h3', 'h4', 'h5'] # list of acceptable tags, this is for eleminating the figure
        end_main_content = ['—','——','———',]               # list of signals which indicate that the main content ends

        author = 'Unknown'
        source = 'Unknown'
        publish_time = 'Unknown'
        source_link = 'Unknown'

        # Extract full content, full content ends by the line '——'
        for i in range(len(content_list)):
            if content_list[i].name in accept_tag and '—' not in content_list[i].text :
                full_content += content_list[i].text + "\n\n"

            # Extract author and original article: 
            # after main content, the information of author and the original article is shown in (i+1)-th element
            # ( Because the i-th element is the line '——')
            elif '—' in content_list[i].text and i+1 < len(content_list):
                # format of information is:
                # <p>Tác giả:...<br>Nguồn:...<br>
                # split it into separate parts: ['Tác giả:...', <br>, 'Nguồn:...', <br>,...] by method `children`
                for child in content_list[i+1].children:
                    if child.name != "br":
                        separate_index = child.text.find(":")+1
                        info = child.text[separate_index:]
                        format_text = " ".join(info.split())
                        if 'tác giả' in child.text.lower():
                            author = format_text
                        if 'nguồn tin' in child.text.lower():
                            source = format_text
                        if 'thời gian' in child.text.lower():
                            publish_time = format_text
                        if 'link' in child.text.lower():
                            source_link = format_text
                break
                
        return {
            "content": full_content,
            "author" : author,
            "source" : source,
            "publish time": publish_time,
            "source link": source_link
        }
                    
    return None

def get_full_information(html_parse) -> dict:
    '''
    Function gets full information of an article
    --> Return: dict:
        {
            "title"                 : str,
            "publisher"             : str,
            "lastest update time"   : str,
            "content"               : str,
            "author"                : str,
            "source"                : str,
            "publish time"          : str,
            "link source"           : str
        }
    '''
    # Get title
    print("\r       Getting title...", end = "")
    title = get_title(html_parse)
    if title:
        title = title[0]
    else: 
        title = 'Unknown'
        print("\r     |X| Cannot get the title !!!")
        
    # Get publisher
    print("\r       Getting publisher...", end = "")
    publiser = get_publisher(html_parse)
    if publiser:
        publiser = ", ".join(publiser)
    else:
        print(("\r    |X| Cannot get the publisher !!!"))
        publiser = 'Unknown'

    # Get latest update time
    print("\r       Getting latest update time...", end="")
    latest_update_time = get_latest_update(html_parse)
    if latest_update_time:
        latest_update_time = " ".join(latest_update_time)
    else:
        print(("\r    |X| Cannot get the latest update time !!!"))
        latest_update_time = 'Unknown'

    # Get content, author, source, publish time, source link
    result = get_content(html_parse)
    print("\r       Getting content, author, source, publish time...", end = "")
    if result:
        result["title"] = title
        result["publisher"] = publiser
        result["latest update time"] = latest_update_time
        print("\r       Finish crawling!                                     ")
        
    else:
        print("\r    |X| Cannot get the content, author, source, publish time!!!")
        return {
            "title"                 : title,
            "publisher"             : publiser,
            "lastest update time"   : latest_update_time,
            "content"               : 'Unknown',
            "author"                : 'Unknown',
            "source"                : 'Unknown',
            "publish time"          : 'Unknown',
            "link source"           : 'Unknown'
        }
        
    return result

def crawl(url, save_file = "save.txt"):
    print("\rCrawling {}".format(url))
    # Send request and receive html text
    if not os.path.exists(save_file):
        html_text = get_html_pass_cloudflare(url)
        with open(save_file, "w", encoding = "utf-8") as f:
            f.write(html_text)
    else:
        with open(save_file, "r", encoding="utf-8") as f:
            html_text = f.read()

    if html_text:
        html_parse = parse_html(html_text)
        result = get_full_information(html_parse)
        
        for key, value in result.items():
            print("{}: {}".format(key, value))
    else:
        print("[FAIL] Cannot access to website!!!")

if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument('--url', type=str, help = 'url')
        args = parser.parse_args()

        crawl(args.url)








