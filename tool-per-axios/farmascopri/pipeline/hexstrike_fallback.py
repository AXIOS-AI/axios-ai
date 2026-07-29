#!/usr/bin/env python3
"""
HexStrike Adapter — Fallback per pipeline farmacie OSINT
Usa Selenium/Chrome come ultima risorsa per trovare siti web 
di farmacie quando FB, IG e web finder falliscono.

Simula ricerca Google/DuckDuckGo via browser.
"""

import json, os, re, time, sys, urllib.parse
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class HexStrikeFallback:
    """Fallback tool: cerca farmacia su Google via browser Selenium"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.results = []
        
    def _init_driver(self):
        if not SELENIUM_OK:
            return False
        if self.driver:
            return True
        try:
            opts = Options()
            if self.headless:
                opts.add_argument('--headless=new')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--disable-gpu')
            opts.add_argument(f'user-agent={USER_AGENT}')
            opts.add_argument('--window-size=1280,720')
            
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=opts)
            return True
        except Exception as e:
            print(f"    ⚠️ Selenium init fail: {str(e)[:60]}")
            return False
    
    def search_google(self, farmacia_nome, citta=''):
        """Cerca su Google per sito web farmacia"""
        if not self._init_driver():
            return []
        
        query = f'sito web {farmacia_nome} {citta} farmacia' if citta else f'sito web {farmacia_nome} farmacia'
        results = []
        
        try:
            self.driver.get('https://www.google.com')
            time.sleep(1)
            
            # Accetta cookies se presente
            try:
                accept_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Accetta") or contains(.,"Accept") or contains(.,"I agree")]'))
                )
                accept_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Cerca
            search_box = self.driver.find_element(By.NAME, 'q')
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)
            
            # Estrai risultati
            for i, result in enumerate(self.driver.find_elements(By.CSS_SELECTOR, 'div.g')[:5]):
                try:
                    a = result.find_element(By.CSS_SELECTOR, 'a[href^="http"]')
                    h3 = result.find_element(By.CSS_SELECTOR, 'h3')
                    snippet_el = result.find_element(By.CSS_SELECTOR, 'div[data-sncf], span.aCOpRe, div.VwiC3b')
                    
                    url = a.get_attribute('href')
                    title = h3.text
                    snippet = snippet_el.text[:200] if snippet_el else ''
                    
                    if url and 'facebook.com' not in url and 'instagram.com' not in url:
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "source": "google_selenium"
                        })
                except:
                    continue
            
        except Exception as e:
            print(f"    ⚠️ Google search error: {str(e)[:60]}")
        
        finally:
            if self.driver:
                try: self.driver.quit()
                except: pass
                self.driver = None
        
        return results[:5]
    
    def search_hexstrike_style(self, farmacia_nome, citta=''):
        """Ricerca combinata multi-motore"""
        results = []
        
        # Prova DuckDuckGo prima (via requests, più veloce)
        try:
            import requests
            from bs4 import BeautifulSoup
            query = f'farmacia {farmacia_nome} {citta} sito web' if citta else f'farmacia {farmacia_nome} sito web'
            r = requests.get('https://html.duckduckgo.com/html/', params={'q': query},
                           headers={'User-Agent': USER_AGENT}, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for res in soup.select('.result')[:5]:
                    a = res.select_one('.result__a')
                    snip = res.select_one('.result__snippet')
                    if a:
                        url = a.get('href', '')
                        m = re.search(r'uddg=(https?://[^&]+)', url)
                        if m:
                            url = urllib.parse.unquote(m.group(1))
                        title = a.get_text(strip=True)
                        desc = snip.get_text(strip=True)[:200] if snip else ''
                        if url and 'duckduckgo.com' not in url and 'facebook.com' not in url and 'instagram.com' not in url:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": desc,
                                "source": "hexstrike_ddg"
                            })
        except:
            pass
        
        # Se DuckDuckGo non dà risultati, prova Google via Selenium
        if not results:
            results = self.search_google(farmacia_nome, citta)
        
        return results[:5]


# =============================================================================
# Funzione per pipeline
# =============================================================================

def hexstrike_find_website(nome, citta='', known_sito=''):
    """Interfaccia per pipeline: cerca sito web come ultima risorsa"""
    result = {
        "farmacia": nome,
        "citta": citta,
        "found": False,
        "best_url": "",
        "attempts": [],
    }
    
    if known_sito:
        result['skipped'] = True
        result['reason'] = 'already_known'
        return result
    
    # 1. DuckDuckGo via requests
    try:
        import requests
        from bs4 import BeautifulSoup
        query = f'farmacia {nome} {citta} sito web' if citta else f'farmacia {nome} sito web'
        r = requests.get('https://html.duckduckgo.com/html/', params={'q': query},
                        headers={'User-Agent': USER_AGENT}, timeout=10)
        if r.status_code == 200 and 'captcha' not in r.text.lower():
            soup = BeautifulSoup(r.text, 'html.parser')
            for res in soup.select('.result')[:5]:
                a = res.select_one('.result__a')
                if a:
                    url = a.get('href', '')
                    m = re.search(r'uddg=(https?://[^&]+)', url)
                    if m:
                        url = urllib.parse.unquote(m.group(1))
                    title = a.get_text(strip=True)[:80]
                    if url and all(x not in url for x in ['facebook','instagram','duckduckgo','youtube','twitter','pinterest']):
                        try:
                            hr = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=6, allow_redirects=True)
                            if hr.status_code == 200:
                                body = hr.text.lower()[:3000]
                                if not any(kw in body for kw in ['parking','nidoma','sito in costruzione','domain is parked','domain for sale']):
                                    result['found'] = True
                                    result['best_url'] = url
                                    result['attempts'].append({"method":"hexstrike_ddg","url":url,"title":title,"status":200})
                                    return result
                        except:
                            pass
    except:
        pass
    
    return result


if __name__ == '__main__':
    # Test
    import json
    r = hexstrike_find_website("Farmacia Puglisi Acate SRL", "Acate")
    print(json.dumps(r, indent=2, ensure_ascii=False))
