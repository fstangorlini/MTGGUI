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
from dataclasses import dataclass
import numpy as np
import os
import json
import queue
import requests
import zipfile
from datetime import datetime
from MTGCard import MTGCard
import random
from PIL import Image


@dataclass
class MTGJson:

    cache_dir_meta:str
    url:str
    json_data:json
    sets:list[str]
    queue_:queue

    def __init__(self, queue_:queue=None):
        self.cache_dir_meta = './cache/metadata/'
        url_base_pre = 'https://mtgjson.com/api/v5/'
        json_file = 'AllSetFiles.zip'
        self.file_extension = '.json'
        self.generated_boosters_json = 'boosters.json'
        self.datetime_format = '%Y-%m-%d %H:%M:%S'
        self.url_composed = url_base_pre+json_file
        self.queue_ = queue_
        if not os.path.isdir(self.cache_dir_meta):os.makedirs(self.cache_dir_meta)
        if not os.path.isfile(self.cache_dir_meta+json_file):
            if self.queue_ is not None: self.queue_.put((0,'Database not found in cache. Downloading...'))
            # Download
            req = requests.get(self.url_composed)
            # save
            with open(self.cache_dir_meta+json_file,'wb') as output_file:
                output_file.write(req.content)
            # Unpack
            if self.queue_ is not None: self.queue_.put((0,'Unpacking database...'))
            with zipfile.ZipFile(self.cache_dir_meta+json_file, 'r') as zip_ref:
                zip_ref.extractall(self.cache_dir_meta)
        self.sets = [f[:-len(self.file_extension)] for f in os.listdir(self.cache_dir_meta) if os.path.isfile(os.path.join(self.cache_dir_meta, f)) and f.endswith(self.file_extension)]

    def generate_booster(self, set_name:str):
        if self.queue_ is not None:  self.queue_.put((0,'Generating a new booster from set ['+set_name+']'))
        if set_name not in self.sets:
            #print(f'Set [{set_name}] could not be found.')
            return None
        # read set json file
        with open(self.cache_dir_meta+set_name+self.file_extension, encoding='UTF-8') as f: set_json_data = json.load(f)
        # get cards
        cards_in_booster = self.__get_booster__(set_json_data)
        # Fetch images
        self.__fetch_images__(cards_in_booster)
        # Fetch all prices
        msg = 'Fetching prices...'
        if self.queue_ is not None: self.queue_.put((1,msg))
        self.__fetch_prices__(cards_in_booster)
        # Save it
        self.__save_booster_to_json__(cards_in_booster, set_json_data)
        # Notify GUI
        msg = '['+set_name+'] booster generated successfully'
        if self.queue_ is not None: self.queue_.put((1,msg))
        print(msg)
        print(f'{cards_in_booster}')
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

    def __get_booster__(self, set_json_data:json):
        # Get propper booster distribution with weights from json [data][booster] info
        boosters = set_json_data['data']['booster']['default']['boosters']
        booster_contents = random.choices(boosters, weights = [w['weight'] for w in boosters], k=1)[0]['contents']
        # Sets up correct rarity order
        key_order = ['basic', 'common', 'uncommon', 'rare', 'rareMythic', 'foil']
        sorted_booster_contents = {}
        for key in key_order:
            if key in booster_contents:
                sorted_booster_contents[key] = booster_contents[key]
        sheets = set_json_data['data']['booster']['default']['sheets']
        cards_in_booster = []
        # Distribution for older sets
        if 'basic' not in list(sorted_booster_contents.keys()):
            for k, v in sorted_booster_contents.items():
                if k=='common':
                    # if there are lands in set
                    lands = list(filter(lambda card: ('Basic Land' in card['type']), set_json_data['data']['cards']))
                    if len(lands)>0:
                        #1 land
                        land = random.sample(lands, k=1)[0]
                        card = MTGCard(list(filter(lambda card: (land['uuid'] == card['uuid']), set_json_data['data']['cards']))[0], self.queue_)
                        cards_in_booster.append(card)
                        #rest common and not land
                        commons_not_lands = list(filter(lambda card: ((card['rarity']==k) and ('Basic Land' not in card['type'])), set_json_data['data']['cards']))
                        commons = random.sample(commons_not_lands, k=v-1)
                    else:
                        commons_not_lands = list(filter(lambda card: ((card['rarity']==k) and ('Basic Land' not in card['type'])), set_json_data['data']['cards']))
                        commons = random.sample(commons_not_lands, k=v)
                    for e in commons:
                        card = MTGCard(list(filter(lambda card: (e['uuid'] == card['uuid']), set_json_data['data']['cards']))[0], self.queue_)
                        cards_in_booster.append(card)
                if k=='uncommon':
                    uncommons_not_lands = list(filter(lambda card: ((card['rarity']==k) and ('Basic Land' not in card['type'])), set_json_data['data']['cards']))
                    uncommons = random.sample(uncommons_not_lands, k=v)
                    for e in uncommons:
                        card = MTGCard(list(filter(lambda card: (e['uuid'] == card['uuid']), set_json_data['data']['cards']))[0], self.queue_)
                        cards_in_booster.append(card)
                if k=='rare':
                    rares_not_lands = list(filter(lambda card: ((card['rarity']==k) and ('Basic Land' not in card['type'])), set_json_data['data']['cards']))
                    rares = random.sample(rares_not_lands, k=v)
                    for e in rares:
                        card = MTGCard(list(filter(lambda card: (e['uuid'] == card['uuid']), set_json_data['data']['cards']))[0], self.queue_)
                        cards_in_booster.append(card)
        # Distribution for newer sets
        else:
            for k, v in sorted_booster_contents.items():
                uuid_list = random.sample(list(sheets[k]['cards'].keys()), counts=[w for w in list(sheets[k]['cards'].values())], k=v)
                for uuid in uuid_list:
                    if k=='foil': is_foil = True
                    else: is_foil = False
                    card = MTGCard(list(filter(lambda card: (uuid == card['uuid']), set_json_data['data']['cards']))[0], self.queue_, foil=is_foil)
                    cards_in_booster.append(card)
        #print(booster_card_uuids)
        return cards_in_booster

    def __get_generated_booster_images__(self):
        return [self.cache_dir_meta+f for f in os.listdir(self.cache_dir_meta) if f.startswith('booster') and f.endswith(self.file_extension)]

    def __save_booster_to_json__(self, booster:list[MTGCard], set_json_data:json):
        data = {}
        # If file does not exist, create it
        if not os.path.isfile(self.cache_dir_meta+self.generated_boosters_json):
            with open(self.cache_dir_meta+self.generated_boosters_json, 'w') as fp:
                json.dump(data, fp, indent = 4)
        # Else, load it
        else:
            with open(self.cache_dir_meta+self.generated_boosters_json, 'r') as file:
                data = json.loads(file.read())
        # Put newly generated booster to file
        now = datetime.now().strftime(self.datetime_format)
        data[now] = self.__get_booster_json__(booster, set_json_data)
        # Save
        with open(self.cache_dir_meta+self.generated_boosters_json, 'w') as fp:
            json.dump(data, fp, indent = 4)

    def __get_booster_json__(self, booster:list[MTGCard], set_json_data:json):
        booster_json = {}
        booster_json['set'] = set_json_data['data']['name']
        booster_json['setCode'] = set_json_data['data']['code']
        booster_json['releaseDate'] = set_json_data['data']['releaseDate']
        booster_json['type'] = set_json_data['data']['type']
        booster_json['cards'] = []
        accum = 0.0
        for card in booster:
            c = {}
            c['name'] = card.name
            c['uuid'] = card.uuid
            c['scryfallId'] = card.scryfallId
            c['rarity'] = card.rarity
            c['foil'] = card.foil
            c['price'] = card.price
            booster_json['cards'].append(c)
            accum += card.price
        booster_json['boosterTotalValue'] = accum
        return booster_json

    def __delete_oldest_image__(self):
        oldest_file = min(self.__get_generated_booster_images__(), key=os.path.getctime)
        os.remove(oldest_file)

    def __control_cache__(self):
        while len(self.__get_generated_booster_images__()) > 15:
            print(f'Cache size too big. Deleting a few previously generated booster images to save some disk space...')
            self.__delete_oldest_image__()

    def display(self, booster_cards:list[MTGCard]):
        if self.queue_ is not None: self.queue_.put((0,'Displaying booster...'))
        if(len(booster_cards)!=15): return False
        img = self.__assemble__(self.__fetch_images__(booster_cards))
        str_date_time = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
        filename = booster_cards[0].cache_dir_img+'booster-'+str_date_time+'.png'
        img.save(filename) #PIL
        img.show() #PIL
        self.__control_cache__() # keeps only a few last generated booster packs not to consume too much space

    def __overlay_image__(self, l_img, s_img, x_offset, y_offset):
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
                img = self.__overlay_image__(img,card_image_list_as_image[i],y,x)
                i+=1
        img = Image.fromarray(img) #PIL
        return img
    
    def __fetch_images__(self, booster_cards:list[MTGCard]):
        card_image_list_as_image = []
        for card in booster_cards:
            card_image_list_as_image.append(card.__get_image__())
        return card_image_list_as_image

    def __fetch_prices__(self, booster_cards:list[MTGCard]):
        for card in booster_cards:
            card.__get_price__()
    