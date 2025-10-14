import os
from pathlib import Path
from urllib.parse import urlunparse

class BrowserController():
    def __init__(self, p):
        self.page = None
        self.browser = None
        self.p = p
        
    def open_browser(self):
        '''
        This function open browser and start a new sesion 
        '''
        try:
            self.browser = self.p.chromium.launch(headless = True)
            self.page = self.browser.new_page()
            return self.browser, self.page
                        
        except Exception as e: 
            print("|X| Exception in open new session: {}".format(e))
            return None
            
    # def closs_browser(self):  
    #     '''
    #     This funtion closes session and browser
    #     '''
    #     try:
    #         self.browser.close()
    #         self.p.stop()
    #     except Exception as e:
    #         print("|X| Exception in closing the browser: {}".format(e))
    
    def access_html(self, html: str):
        '''
        This function accesses and shows html file to extract information
        '''
        # Check if parameter html is a file
        if html.endswith(".html"):
            # Get the absolute path to current file
            base_dir = Path(__file__).resolve().parent 
            file_path = base_dir / html
            
            if os.path.exists(file_path):
                print("/ Showing html file {} ...".format(html))
                # format file path to the form which can be read be playwright
                file_url = urlunparse(('file', '', str(file_path).replace(os.path.sep, '/'), '', '', ''))
                self.page.goto(file_url, wait_until="networkidle")
                return True
            else:
                print("|X| (!_!) Access Fail: File {} is not existed".format(file_path))
                return False
        
        elif html.startswith("http"):
                try:
                    print("/ Accessing the url {} ...".format(html))
                    self.page.goto(html, wait_util="networkidle")
                    return True
                except Exception as e:
                    print("|X| (*_*) Access Fail: {}".format(e))
                    return False