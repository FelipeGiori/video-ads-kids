# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import re
import sys
import pickle
import threading
from datetime import datetime
from time import sleep, time
from selenium import webdriver
from random import uniform
from pyvirtualdisplay import Display
from log import send2db


class Webdriver(threading.Thread):    
    def __init__ (self, persona):
        threading.Thread.__init__(self)
        
        # Persona info setup
        self.id = persona.id
        self.email = persona.email
        self.password = persona.password
        self.session_time = persona.session_time # em horas
        self.skip_topic = 0.35
        self.skip_offtopic = 0.35
        self.p_train = 1
        self.display = Display(visible = False, size=(800, 600), backend='xvfb').start()
        self.driver = self.setup_driver()
    
    def run(self):
        print("Run")
        self.login_youtube()
        topic_urls = self.get_subscribed_playlist()
        offtopic_urls = self.get_subscribed_playlist()
        self.browse(topic_urls, offtopic_urls)
        self.save_cookies()
        self.quit()


    # Browser init
    def setup_driver(self):
        profile = webdriver.FirefoxProfile()
        
        try:
            driver = webdriver.Firefox(firefox_profile = profile)
        except:
            print('Erro ao inicializar o Firefox. Abortando Thread...')
            sys.exit()

        driver.get('https://www.youtube.com/')
        self.check_folder_exists()
        self.load_cookies(driver)
        return driver    
    
    # Check if the necessary folders exist
    def check_folder_exists(self):
        directory = "personas/"
        if not(os.path.isdir(directory)):
            os.makedirs(directory)

        directory = "personas/" + self.email
        if not(os.path.isdir(directory)):
            os.makedirs(directory)
    
        
    def load_cookies(self, driver):
        path_file = 'personas/' + self.email + '/' + self.email + '.pkl'
        if(os.path.isfile(path_file)):
            cookies = pickle.load(open(path_file, 'rb'))
            for cookie in cookies:
                driver.add_cookie(cookie)
    

    def login_youtube(self):
        self.driver.get('https://accounts.google.com/')
        self.driver.find_element_by_id('identifierId').send_keys(self.email)
        self.driver.find_element_by_id('identifierNext').click()
        self.driver.window_handles[0]
        sleep(10) # Espera a transição de formulário
        self.driver.find_element_by_name('password').send_keys(self.password)
        self.driver.find_element_by_id('passwordNext').click()
        sleep(5)
        
        # TODO: Change login auth
        logged_in_url = "https://myaccount.google.com/?pli=1"
        if(self.driver.current_url == logged_in_url):
            self.driver.get('https://youtube.com')
            return True
        else:
            print("Could not log in")
            return False

    # Only works if the user is logged in
    def get_subscribed_playlist(self):
        self.driver.get('https://www.youtube.com/feed/subscriptions')
        sleep(2)
        html_source = self.driver.page_source
        
        try:
            a = re.compile('{"simpleText":"Today"}(.*){"simpleText":"Yesterday"}')
            today_html = a.search(html_source)
        
            if(today_html == None):
                a = re.compile('{"simpleText":"Hoje"}(.*){"simpleText":"Ontem"}')
                today_html = a.search(html_source)
                b = re.compile('{"videoId":"(.+?)"')
                playlist = b.findall(today_html.group(1))
            else:    
                b = re.compile('{"videoId":"(.+?)"')
                playlist = b.findall(today_html.group(1))
                playlist = list(set(playlist))
        except:
            print("Could not build playlist")
            self.quit()
        
        return list(set(playlist))


    # Start youtube browsing
    def browse(self, topic_urls, offtopic_urls):

        # seconds * minutes * hours
        timeout = time() + 60 * 60 * self.session_time
        i, j = 0, 0

        while(time() < timeout):
            if(i == len(topic_urls) or j == len(offtopic_urls)):
                print(self.email + ' does not have more videos to watch')
                break
                
            # Dada a probabilidade da persona, um número real entre 0 e 1 é gerado.
            # Se o número gerado for menor ou igual a probabilidade de treino da persona,
            # um vídeo da lista de treino será visto. Caso contrário, um vídeo da lista
            # de teste será visto.
            if(uniform(0, 1) <= self.p_train and i < len(topic_urls)):
                self.watch(topic_urls[i], self.skip_topic)
                i += 1
                    
            elif(j < len(offtopic_urls)):
                self.watch(offtopic_urls[j], self.skip_offtopic)
                j += 1
        
    
    def watch(self, video_id, skip):
        WATCH_TIME_LIMIT = 10*60 # 10 minutos
        timeout = time() + WATCH_TIME_LIMIT
        
        start_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        send2db(self.id, start_time, video_id, '', 'STARTED WATCHING VCONTENT')
        
        video_url = "https://www.youtube.com/watch?v=" + video_id
        self.driver.get(video_url)
        
        while(self.player_status() is None):
            if(timeout < time()):
                break # Waiting for the video player...
            else:
                sleep(2)
        
        # If skip is True, Skips the video-ad
        # If skip is False, watch the whole video-ad
        if(self.player_status() == -1):
            time_start = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            send2db(self.id, time_start, video_id, '', 'STARTED WATCHING AD')            
            self.watching_ad(skip, video_id, timeout)

        # Check if the video streaming has finished
        if(self.player_status() != 0 and self.player_status() != 5): 
            while(self.player_status() != 0 and self.driver.current_url.find('watch?v=') != -1):
                if(timeout < time()):
                    break
                else:
                    sleep(3)
                
                try:
                    self.driver.find_element_by_css_selector('.videoAdUiSkipButton').click()
                    time_now = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    send2db(self.id, time_now, video_id, '', 'AD SKIPPED MID VCONTENT')
                except:
                    pass
        
        end_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        send2db(self.id, end_time, video_id, '', 'FINISHED WATCHING VCONTENT')                
    
    # Returns the video player current state
    def player_status(self):

        # Video player state code
        #  1: Video-Content being streamed
        #  2: Video paused
        #  5: Video has been removed
        #  0: Video streaming finished
        # -1: Video-Ad being streamed

        try:
            status = self.driver.execute_script("return document.getElementById('movie_player').getPlayerState()")
        except :
            status = None
        
        return status
        
    
    def watching_ad(self, skip, video_id, timeout):
        if(uniform(0, 1) <= skip): 
            self.skip_ad(video_id, timeout)
        else: 
            while(self.player_status() == -1 and self.driver.current_url.find('watch?v=')):
                if(timeout < time()):
                    break
                else:
                    sleep(2)
            time_now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            send2db(self.id, time_now, video_id, '', 'FINISHED WATCHING AD')

    def skip_ad(self, video_id, timeout):
        while(self.player_status() == -1):
            if(timeout < time()):
                break
            else:
                try:
                    self.driver.find_element_by_css_selector('.videoAdUiSkipButton').click()
                    time_now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    send2db(self.id, time_now, video_id, '', 'AD SKIPPED')
                    return 0
                except Exception as _:
                    sleep(2)
    
            
    def save_cookies(self):
        pickle.dump(self.driver.get_cookies(), open('personas/' + self.email + '/' + self.email + '.pkl', 'wb'))
        
    
    def quit(self):
        self.driver.close()
        self.display.popen.terminate()
