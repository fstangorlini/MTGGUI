###############################################################################
######################### Author:  Felipe Stangorlini #########################
######################### Date:    Aug-2022           #########################
######################### Version: 0.1                #########################
###############################################################################

#Database source
#https://mtgjson.com/

#Image source
#https://scryfall.com/docs/api

######################################################################################################
# Imports
from tkinter import ttk
from tkinter import *
import tkinter as tk
import queue
import threading
from dataclasses import dataclass
import json
import os
from tkinter.font import BOLD
import requests
import zipfile
import random
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime

######################################################################################################
# Classes
class ThreadedTask(threading.Thread):

    def __init__(self, queue_:queue, set_name:str):
        threading.Thread.__init__(self)
        self.queue_ = queue_
        self.set_name = set_name
        
    def run(self):
        #Worker(self.queue_,self.fileX,self.fileY)
        m = Mtgjson(self.queue_)
        booster = m.generate_booster(self.set_name)
        self.queue_.put((2,booster))

@dataclass
class Card:

    name:str
    type:str
    set:str
    rarity:str
    uuid:str
    image_url:str
    rarity_converter = {}
    cache_dir_img:str
    image_resolution:str
    queue_:queue
    image:Image

    def __init__(self,json_data:json, queue_:queue):
        #print(f'Initializing Card:\n{json_data}')
        self.image_resolution = 'normal' #small, normal, large, png, art_crop, or border_crop. Defaults to large.
        self.rarity_converter = {'mythic':'M','rare':'R','uncommon':'U','common':'C'}
        self.cache_dir_img = './cache/img/'
        self.file_extension = '.png'
        self.queue_ = queue_
        #print(f'Initializing card {name}')
        if json_data is not None:
            self.name = json_data['name']
            self.set = json_data['setCode']
            self.uuid = json_data['identifiers']['scryfallId']
            self.image_url = 'https://api.scryfall.com/cards/'+self.uuid+'?format=image&face=front&version='+self.image_resolution
            self.rarity = json_data['rarity']
            self.type = json_data['type']
        if not os.path.isdir(self.cache_dir_img): os.makedirs(self.cache_dir_img)

    def __get_image__(self):
        if(os.path.isfile(self.cache_dir_img+self.uuid+self.file_extension)):
            img = Image.open(self.cache_dir_img+self.uuid+self.file_extension)
            self.image = img
            return img
        else:
            print(f'Image [{self.name}] not in cache. Fetching from {self.image_url}',end='. ')
            self.queue_.put((0,'Image ['+self.name+'] not in cache. Fetching from '+self.image_url))
            try:
                img = Image.open(requests.get(self.image_url, stream=True).raw)
                img.save(self.cache_dir_img+self.uuid+self.file_extension)
                print('OK!')
                self.queue_.put((0,'OK!'))
            except:
                print('NOK')
                self.queue_.put((0,'Error downloading...'))
                img = Image.open('./res/mtg-card-back.png')
            self.image = img
            return img

    def __str__(self):
        ret = '-----------------------------------'
        ret = ret + '\n[Name]\t\t' + self.name
        ret = ret + '\n[Set]\t\t' + self.set
        ret = ret + '\n[Rarity]\t' + self.rarity
        ret = ret + '\n[Url]\t\t' + self.image_url
        ret+= '\n-----------------------------------\n'
        return ret

    def __repr__(self):
        return self.name

@dataclass
class Mtgjson:

    cache_dir:str
    url:str
    json_data:json
    sets:list[str]
    queue_:queue

    def __init__(self, queue_:queue):
        self.cache_dir = './cache/metadata/'
        url_base_pre = 'https://mtgjson.com/api/v5/'
        json_file = 'AllSetFiles.zip'
        self.file_extension = '.json'
        self.url_composed = url_base_pre+json_file
        self.queue_ = queue_
        if not os.path.isdir(self.cache_dir):os.makedirs(self.cache_dir)
        if not os.path.isfile(self.cache_dir+json_file):
            self.queue_.put((0,'Database not found in cache. Downloading...'))
            # Download
            req = requests.get(self.url_composed)
            # save
            with open(self.cache_dir+json_file,'wb') as output_file:
                output_file.write(req.content)
            # Unpack
            self.queue_.put((0,'Unpacking database...'))
            with zipfile.ZipFile(self.cache_dir+json_file, 'r') as zip_ref:
                zip_ref.extractall(self.cache_dir)
        self.sets = [f[:-len(self.file_extension)] for f in os.listdir(self.cache_dir) if os.path.isfile(os.path.join(self.cache_dir, f)) and f.endswith(self.file_extension)]

    def generate_booster(self, set_name:str):
        self.queue_.put((0,'Generating a new booster from set ['+set_name+']'))
        if set_name not in self.sets:
            #print(f'Set [{set_name}] could not be found.')
            return None
        with open(self.cache_dir+set_name+self.file_extension, encoding='UTF-8') as f: json_data = json.load(f)
        card_distribution = {'rare':1,'uncommon':3,'common':10,'Basic Land':1} #15 total
        cards_in_booster = []
        rares = self.__get_cards_by_rarity__('rare',json_data)
        uncommons = self.__get_cards_by_rarity__('uncommon',json_data)
        commons = self.__get_cards_by_rarity__('common',json_data)
        basic_lands = self.__get_cards_by_rarity__('Basic Land', json_data)
        rc={'rare':rares,'uncommon':uncommons,'common':commons,'Basic Land':basic_lands}
        for rarity, quantity in card_distribution.items():
            cards_in_booster.extend(random.sample(self.__get_cards_by_rarity__(rarity,json_data), k=quantity))
        #self.display(cards_in_booster)
        self.__fetch_images__(cards_in_booster)
        self.queue_.put((1,'Booster generated successfully'))
        return cards_in_booster
    
    def __get_card_by_name__(self, card_name:str, json_data:json):
        '''
        #Non pythonic way
        cards = json_data['data']['cards']
        for card in cards:
            if card['name']==card_name: return card
        return []
        '''
        # Pythonic way
        return list(filter(lambda card: card['name'] == card_name, json_data['data']['cards']))
    
    def __get_cards_by_rarity__(self, rarity:str, json_data:json):
        card_list = []
        #TODO implement mythic
        if rarity in ['rare','uncommon','common']: 
            for json_card in list(filter(lambda card: ((card['rarity'] == rarity) and ('Basic Land' not in card['type'])), json_data['data']['cards'])):
                card_list.append(Card(json_card, self.queue_))
        if rarity in ['Basic Land']:
            for json_card in list(filter(lambda card: ('Basic Land' in card['type']), json_data['data']['cards'])):
                card_list.append(Card(json_card, self.queue_))
        return card_list
    
    def __get_generated_booster_images__(self):
        return [self.cache_dir+f for f in os.listdir(self.cache_dir) if f.startswith('booster') and f.endswith(self.file_extension)]

    def __delete_oldest_image__(self):
        oldest_file = min(self.__get_generated_booster_images__(), key=os.path.getctime)
        os.remove(oldest_file)

    def __control_cache__(self):
        while len(self.__get_generated_booster_images__()) > 15:
            print(f'Cache size too big. Deleting a few previously generated booster images to save some disk space...')
            self.__delete_oldest_image__()

    def display(self, booster_cards:list[Card]):
        self.queue_.put((0,'Displaying booster...'))
        if(len(booster_cards)!=15): return False
        img = self.__assemble__(self.__fetch_images__(booster_cards))
        str_date_time = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
        filename = booster_cards[0].cache_dir_img+'booster-'+str_date_time+'.png'
        img.save(filename) #PIL
        #img.show() #PIL
        self.__control_cache__() # keeps only a few last generated booster packs not to consume too much space

    def __overlay_image__(self, l_img, s_img, x_offset, y_offset):
        #print(f'overlay_image')
        #print(f'l_img=({l_img.shape[0]},{l_img.shape[1]})')
        #print(f's_img=({s_img.shape[0]},{s_img.shape[1]})')
        #height = s_img.shape[0] #cv2
        #width = s_img.shape[1] #cv2
        height = s_img.height #PIL
        width = s_img.width #PIL
        l_img[y_offset:y_offset+height, x_offset:x_offset+width] = s_img
        return l_img

    def __assemble__(self, card_image_list_as_image:list):
        x_spacing = 50
        y_spacing = 50
        rows = [0,1,2]
        cols = [0,1,2,3,4]
        x_max = 0
        y_max = 0
        for card_image in card_image_list_as_image:
            #height = card_image.shape[0] #cv2
            #width = card_image.shape[1] #cv2
            height = card_image.height #PIL
            width = card_image.width #PIL
            if x_max < height: x_max = height
            if y_max < width: y_max = width
        x_full_length = (x_max*len(rows))+(len(rows)*x_spacing)+x_spacing
        y_full_length = (y_max*len(cols))+(len(cols)*y_spacing)+y_spacing
        img = np.zeros([x_full_length,y_full_length,3],dtype=np.uint8)
        #img.fill(255) #make image white
        i=0
        for col in cols:
            for row in rows:
                card_image = card_image_list_as_image[i]
                height = card_image.height #PIL
                width = card_image.width #PIL
                x = x_spacing+(x_spacing*row)+(row*height)
                y = y_spacing+(y_spacing*col)+(col*width)
                #print(f'(r{row},c{col} -> overlay at ({x},{y})')
                img = self.__overlay_image__(img,card_image_list_as_image[i],y,x)
                i+=1
        img = Image.fromarray(img) #PIL
        return img
    
    def __fetch_images__(self, booster_cards:list[Card]):
        card_image_list_as_image = []
        for card in booster_cards:
            card_image_list_as_image.append(card.__get_image__())
        return card_image_list_as_image

######################################################################################################
# GUI
class MTGGUI(tk.Frame):
    
    queue_:queue
    image_list:list
    
    def __action_button_generate__(self):
        self.__disable_buttons__()
        self.progress_bar.start()
        ThreadedTask(self.queue_,self.stringvar_sets.get()).start()
        return
    
    def __action_button_next__(self):
        if self.display_index >= 15: self.display_index = 0
        self.display_index+=1
        self.__update_images__()
        return
    
    def __action_button_prev__(self):
        if self.display_index <= 1: self.display_index = 16
        self.display_index-=1
        self.__update_images__()
        return
    
    def __disable_buttons__(self):
        self.button_generate.config(state='disabled')
        self.button_next.config(state='disabled')
        self.button_prev.config(state='disabled')
    
    def __enable_buttons__(self):
        self.button_generate.config(state='normal')
        self.button_next.config(state='normal')
        self.button_prev.config(state='normal')
    
    def __populate_image_list__(self, booster:list[Card]):
        self.images.append((self.img_card_back[0],self.img_card_back[1]))
        for card in booster:
            s = card.image.resize(self.corner_card_size)
            l = card.image.resize(self.centered_card_size)
            self.images.append((s,l))
        self.images.append((self.img_card_back[0],self.img_card_back[1]))
    
    def __update_image__(self, label:Label, image:Image):
        img = ImageTk.PhotoImage(image)
        label.configure(image = img)
        label.image = img

    def __update_images__(self):
        if(len(self.images)!=17):
            self.__update_image__(self.label_img_mid, self.img_card_back[1])
            self.__update_image__(self.label_img_left, self.img_card_back[0])
            self.__update_image__(self.label_img_right, self.img_card_back[0])
        else:
            self.__update_image__(self.label_img_mid, self.images[self.display_index][1])
            self.__update_image__(self.label_img_left, self.images[self.display_index-1][0])
            self.__update_image__(self.label_img_right, self.images[self.display_index+1][0])

    def __process_queue__(self):
        msg = None
        if(self.queue_.empty()==False):
            msg = self.queue_.get(0)
            if(msg[0]==1):
                self.progress_bar.stop()
                self.__enable_buttons__()
            if(msg[0]==2):
                self.booster = msg[1]
                self.__populate_image_list__(self.booster)
                self.__update_images__()
        return msg
    
    def __update_root__(self):
        self.root.after(100, self.__update_root__)
        if(self.queue_.empty()==False):
            msg = self.__process_queue__()
            self.textfield_status.delete(0,END)
            self.textfield_status.insert(0,msg[1])
    
    def __custom_init__(self):
        #######################################################################
        # Define root window properties
        self.root.title(self.TITLE)
        self.root.geometry(self.GEOMETRY)
        self.root.resizable(False, False)
        
        #######################################################################
        # Create elements        
        self.label_subtitle         = Label(self.root,text=self.SUBTITLE,font=("Segoe UI", 16, BOLD))
        self.textfield_status       = Entry(self.root,width=105,textvariable=self.stringvar_text_status)
        self.stringvar_text_status  = StringVar()
        self.stringvar_sets         = StringVar()
        self.progress_label         = Label(self.root,text=self.label_progress,font=("Segoe UI", 10))
        self.progress_bar           = ttk.Progressbar(orient="horizontal",length=self.width, mode="determinate")
        self.label_sets             = Label(self.root,text='Set',width=7,font=("Segoe UI", 10))
        self.label_img_mid          = Label(self.root)
        self.label_img_left         = Label(self.root)
        self.label_img_right        = Label(self.root)
        self.entry_sets             = Entry(self.root,width=7,textvariable=self.stringvar_sets)
        self.button_generate        = Button(self.root,text='Generate',command=self.__action_button_generate__, width=16)
        self.button_next            = Button(self.root,text='Next',command=self.__action_button_next__, width=16)
        self.button_prev            = Button(self.root,text='Previous',command=self.__action_button_prev__, width=16)
        
    def __align_elements__(self):
        #######################################################################
        # Align elements to grid
        self.label_subtitle.place(x=110,y=10)
        self.label_sets.place(x=160,y=57)
        self.entry_sets.place(x=210,y=60)
        self.button_generate.place(x=290,y=57)
        self.progress_bar.place(x=0,y=self.height-10)
        self.textfield_status.place(x=0,y=self.height-30)
        self.label_img_mid.place(x=150,y=100)
        self.label_img_left.place(x=5,y=self.width/2-(self.corner_card_size[1]/2))
        self.label_img_right.place(x=self.width-(self.corner_card_size[0])-5,y=self.width/2-(self.corner_card_size[1]/2))
        self.button_next.place(x=500,y=500)
        self.button_prev.place(x=15,y=500)

    def __post_init__(self):
        #######################################################################
        # Post
        self.textfield_status.delete(0,END)
        self.textfield_status.insert(0,'Please inform Set code and click Generate button. (I.E. LEA = Legacy Alpha)')
        self.entry_sets.insert(0,'LEA')
        self.textfield_status.config(state='disabled')
        self.button_next.config(state='disabled')
        self.button_prev.config(state='disabled')
        self.__update_images__()
        self.root.after(100, self.__update_root__)
        self.root.mainloop()

    def __init__(self, queue_):
        #######################################################################
        # Variables
        self.queue_ = queue_
        self.root = tk.Tk()
        super().__init__(self.root)
        self.pack()
        self.images = []
        self.width = 630
        self.height = 620
        self.centered_card_size = (330,460)
        self.corner_card_size   = (138,192)
        self.GEOMETRY = str(self.width)+'x'+str(self.height)
        self.TITLE = 'Magic the Gathering - Booster Generator'
        self.SUBTITLE = self.TITLE
        self.SETS = ['10E', '2ED', '2X2', '2XM', '3ED', '40K', '4BB', '4ED', '5DN', 
                     '5ED', '6ED', '7ED', '8ED', '9ED', 'A25', 'AAFR', 'ACLB', 'AER', 
                     'AFC', 'AFR', 'AJMP', 'AKH', 'AKHM', 'AKR', 'ALA', 'ALL', 'AMH1', 
                     'AMH2', 'AMID', 'ANA', 'ANB', 'ANEO', 'APC', 'ARB', 'ARC', 'ARN', 
                     'ASNC', 'ASTX', 'ATH', 'ATQ', 'AVOW', 'AVR', 'AZNR', 'BBD', 'BFZ', 
                     'BNG', 'BOK', 'BRB', 'BRO', 'BTD', 'C13', 'C14', 'C15', 'C16', 'C17', 
                     'C18', 'C19', 'C20', 'C21', 'CC1', 'CC2', 'CED', 'CEI', 'CHK', 'CHR', 
                     'CLB', 'CM1', 'CM2', 'CMA', 'CMB1', 'CMB2', 'CMD', 'CMR', 'CN2', 'CNS', 
                     'CON_', 'CP1', 'CP2', 'CP3', 'CSP', 'CST', 'DBL', 'DD1', 'DD2', 'DDC', 
                     'DDD', 'DDE', 'DDF', 'DDG', 'DDH', 'DDI', 'DDJ', 'DDK', 'DDL', 'DDM', 
                     'DDN', 'DDO', 'DDP', 'DDQ', 'DDR', 'DDS', 'DDT', 'DDU', 'DGM', 'DIS', 
                     'DKA', 'DKM', 'DMC', 'DMR', 'DMU', 'DOM', 'DPA', 'DRB', 'DRK', 'DST', 
                     'DTK', 'DVD', 'E01', 'E02', 'EA1', 'ELD', 'EMA', 'EMN', 'EVE', 'EVG', 
                     'EXO', 'EXP', 'F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 
                     'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 
                     'FBB', 'FEM', 'FJMP', 'FMB1', 'FNM', 'FRF', 'FUT', 'G00', 'G01', 'G02', 
                     'G03', 'G04', 'G05', 'G06', 'G07', 'G08', 'G09', 'G10', 'G11', 'G17', 
                     'G18', 'G99', 'GDY', 'GK1', 'GK2', 'GN2', 'GN3', 'GNT', 'GPT', 'GRN', 
                     'GS1', 'GTC', 'GVL', 'H09', 'H17', 'H1R', 'HA1', 'HA2', 'HA3', 'HA4', 
                     'HA5', 'HA6', 'HBG', 'HHO', 'HML', 'HOP', 'HOU', 'HTR16', 'HTR17', 'HTR18', 
                     'HTR19', 'HTR20', 'ICE', 'IKO', 'IMA', 'INV', 'ISD', 'ITP', 'J12', 'J13', 
                     'J14', 'J15', 'J16', 'J17', 'J18', 'J19', 'J20', 'J21', 'JGP', 'JMP', 'JOU', 
                     'JUD', 'JVC', 'KHC', 'KHM', 'KLD', 'KLR', 'KTK', 'L12', 'L13', 'L14', 'L15', 
                     'L16', 'L17', 'LEA', 'LEB', 'LEG', 'LGN', 'LRW', 'M10', 'M11', 'M12', 'M13', 
                     'M14', 'M15', 'M19', 'M20', 'M21', 'MAFR', 'MB1', 'MBS', 'MD1', 'ME1', 'ME2', 
                     'ME3', 'ME4', 'MED', 'MGB', 'MH1', 'MH2', 'MIC', 'MID', 'MIR', 'MKHM', 'MM2', 
                     'MM3', 'MMA', 'MMH2', 'MMQ', 'MOR', 'MP2', 'MPR', 'MPS', 'MRD', 'MSTX', 'MVOW', 
                     'MZNR', 'NCC', 'NEC', 'NEM', 'NEO', 'NPH', 'O90P', 'OAFC', 'OANA', 'OARC', 'OC13', 
                     'OC14', 'OC15', 'OC16', 'OC17', 'OC18', 'OC19', 'OC20', 'OC21', 'OCM1', 'OCMD', 
                     'ODY', 'OE01', 'OGW', 'OHOP', 'OLEP', 'OLGC', 'OMIC', 'ONS', 'OPC2', 'OPCA', 'ORI', 
                     'OVNT', 'OVOC', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P10E', 
                     'P11', 'P15A', 'P22', 'P2HG', 'P30A', 'P30H', 'P5DN', 'P8ED', 'P9ED', 'PAER', 'PAFR', 
                     'PAKH', 'PAL00', 'PAL01', 'PAL02', 'PAL03', 'PAL04', 'PAL05', 'PAL06', 'PAL99', 'PALA', 
                     'PALP', 'PANA', 'PAPC', 'PARB', 'PARC', 'PARL', 'PAST', 'PAVR', 'PBBD', 'PBFZ', 'PBNG', 
                     'PBOK', 'PBOOK', 'PC2', 'PCA', 'PCEL', 'PCHK', 'PCLB', 'PCMD', 'PCMP', 'PCNS', 'PCON', 
                     'PCSP', 'PCY', 'PD2', 'PD3', 'PDGM', 'PDIS', 'PDKA', 'PDMU', 'PDOM', 'PDP10', 'PDP12', 
                     'PDP13', 'PDP14', 'PDP15', 'PDRC', 'PDST', 'PDTK', 'PDTP', 'PELD', 'PELP', 'PEMN', 'PEVE', 
                     'PEXO', 'PF19', 'PF20', 'PF21', 'PFRF', 'PFUT', 'PG07', 'PG08', 'PGPT', 'PGPX', 'PGRN', 
                     'PGRU', 'PGTC', 'PGTW', 'PHED', 'PHEL', 'PHJ', 'PHOP', 'PHOU', 'PHPR', 'PHUK', 'PI13', 
                     'PI14', 'PIDW', 'PIKO', 'PINV', 'PISD', 'PJ21', 'PJAS', 'PJJT', 'PJOU', 'PJSE', 'PJUD', 
                     'PKHM', 'PKLD', 'PKTK', 'PL21', 'PL22', 'PLC', 'PLG20', 'PLG21', 'PLG22', 'PLGM', 'PLGN', 
                     'PLIST', 'PLNY', 'PLRW', 'PLS', 'PM10', 'PM11', 'PM12', 'PM13', 'PM14', 'PM15', 'PM19', 
                     'PM20', 'PM21', 'PMBS', 'PMEI', 'PMH1', 'PMH2', 'PMIC', 'PMID', 'PMMQ', 'PMOA', 'PMOR', 
                     'PMPS', 'PMPS06', 'PMPS07', 'PMPS08', 'PMPS09', 'PMPS10', 'PMPS11', 'PMRD', 'PNAT', 'PNCC', 
                     'PNEM', 'PNEO', 'PNPH', 'PODY', 'POGW', 'PONS', 'POR', 'PORI', 'PPC1', 'PPCY', 'PPLC', 'PPLS', 
                     'PPP1', 'PPRO', 'PPTK', 'PR2', 'PRAV', 'PRCQ', 'PRED', 'PRES', 'PRIX', 'PRM', 'PRNA', 'PROE', 
                     'PRTR', 'PRW2', 'PRWK', 'PS11', 'PS14', 'PS15', 'PS16', 'PS17', 'PS18', 'PS19', 'PSAL', 'PSCG', 
                     'PSDC', 'PSDG', 'PSHM', 'PSNC', 'PSOI', 'PSOK', 'PSOM', 'PSS1', 'PSS2', 'PSS3', 'PSTH', 'PSTX', 
                     'PSUM', 'PSUS', 'PSVC', 'PTC', 'PTG', 'PTHB', 'PTHS', 'PTK', 'PTKDF', 'PTMP', 'PTOR', 'PTSNC', 
                     'PTSP', 'PUDS', 'PULG', 'PUMA', 'PUNH', 'PURL', 'PUSG', 'PUST', 'PVAN', 'PVOW', 'PW09', 'PW10', 
                     'PW11', 'PW12', 'PW21', 'PW22', 'PWAR', 'PWOR', 'PWOS', 'PWPN', 'PWWK', 'PXLN', 'PXTC', 'PZ1', 
                     'PZ2', 'PZEN', 'PZNR', 'Q06', 'RAV', 'REN', 'RIN', 'RIX', 'RNA', 'ROE', 'RQS', 'RTR', 'S00', 'S99', 
                     'SCG', 'SCH', 'SHM', 'SKHM', 'SLD', 'SLU', 'SLX', 'SMID', 'SNC', 'SOI', 'SOK', 'SOM', 'SS1', 'SS2', 
                     'SS3', 'SSTX', 'STA', 'STH', 'STX', 'SUM', 'SUNF', 'SVOW', 'SZNR', 'TBTH', 'TD0', 'TD2', 'TDAG', 
                     'TFTH', 'THB', 'THP1', 'THP2', 'THP3', 'THS', 'TMP', 'TOR', 'TPR', 'TSB', 'TSP', 'TSR', 'UDS', 
                     'UGIN', 'UGL', 'ULG', 'UMA', 'UND', 'UNF', 'UNH', 'USG', 'UST', 'V09', 'V10', 'V11', 'V12', 'V13', 
                     'V14', 'V15', 'V16', 'V17', 'VIS', 'VMA', 'VOC', 'VOW', 'W16', 'W17', 'WAR', 'WC00', 'WC01', 'WC02', 
                     'WC03', 'WC04', 'WC97', 'WC98', 'WC99', 'WMC', 'WTH', 'WWK', 'XANA', 'XLN', 'YMID', 'YNEO', 'YSNC', 
                     'ZEN', 'ZNC', 'ZNE', 'ZNR']
        self.label_progress = 'Progress'
        self.img_card_back = Image.open('./res/mtg-card-back.png')
        self.img_card_back = (self.img_card_back.resize(self.corner_card_size),self.img_card_back.resize(self.centered_card_size))
        self.display_index = 1
        self.__custom_init__()
        self.__align_elements__()
        self.__post_init__()
       
# Initialize
g = MTGGUI(queue.Queue())
