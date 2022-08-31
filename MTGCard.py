###############################################################################
######################### Author:  Felipe Stangorlini #########################
######################### Date:    Aug-2022           #########################
######################### Version: 0.1                #########################
###############################################################################

#Database source
#https://mtgjson.com/

#Image source
#https://scryfall.com/docs/api

from dataclasses import dataclass
import queue
import json
from PIL import Image
import requests
import os

@dataclass
class MTGCard:

    uuid:str
    name:str
    type:str
    set_code:str
    rarity:str
    scryfallId:str
    image_url:str
    image_resolution:str
    image:Image
    foil:bool
    price:float

    def __init__(self, card_json_data:json, queue_:queue=None, foil:bool=False):
        self.image_resolution = 'normal' #small, normal, large, png, art_crop, or border_crop. Defaults to large.
        self.cache_dir_img = './cache/img/'
        self.cache_dir_meta = './cache/metadata/'
        self.res_dir = './res/'
        self.file_extension = '.png'
        self.prices_json_file = 'prices.json'
        self.prices_json = None
        self.queue_ = queue_
        self.foil = foil
        self.price = 0.0
        self.card_print_separator = '--------------------------------------------------'
        if card_json_data is not None:
            self.uuid = card_json_data['uuid']
            self.name = card_json_data['name']
            self.set_code = card_json_data['setCode']
            self.scryfallId = card_json_data['identifiers']['scryfallId']
            self.image_url = 'https://api.scryfall.com/cards/'+self.scryfallId+'?format=image&face=front&version='+self.image_resolution
            self.price_url = 'https://api.scryfall.com/cards/'+self.scryfallId
            self.rarity = card_json_data['rarity']
            self.type = card_json_data['type']
        if not os.path.isdir(self.cache_dir_img): os.makedirs(self.cache_dir_img)

    def __get_image__(self):
        if(os.path.isfile(self.cache_dir_img+self.scryfallId+self.file_extension)):
            img = Image.open(self.cache_dir_img+self.scryfallId+self.file_extension)
            if self.foil:
                img = self.__apply_foil__(img)
        else:
            print(f'Image [{self.name}] not in cache. Fetching from {self.image_url}',end='. ')
            if self.queue_ is not None: self.queue_.put((0,'Image ['+self.name+'] not in cache. Fetching from '+self.image_url))
            try:
                img = Image.open(requests.get(self.image_url, stream=True).raw)
                if self.foil: img = self.__apply_foil__(img)
                img.save(self.cache_dir_img+self.scryfallId+self.file_extension)
                print('OK!')
                if self.queue_ is not None: self.queue_.put((0,'OK!'))
            except:
                print('NOK')
                if self.queue_ is not None: self.queue_.put((0,'Error downloading...'))
                img = Image.open('./res/mtg-card-back.png')
        self.image = img
        return img

    def __get_price__(self):
        prices = {}
        if not os.path.isfile(self.cache_dir_meta+self.prices_json_file):
            with open(self.cache_dir_meta+self.prices_json_file, 'w') as fp:
                json.dump(prices, fp, indent = 4)
        else:
            with open(self.cache_dir_meta+self.prices_json_file, 'r') as file:
                prices = json.loads(file.read())
        # From cache
        if self.scryfallId in prices:
            self.prices_json = prices[self.scryfallId]
        # From API
        else:
            card_json = requests.get(self.price_url, stream=True).json()
            card_json_light = {}
            card_json_light['usd_foil'] = card_json['prices']['usd_foil']
            card_json_light['usd'] = card_json['prices']['usd']
            prices[self.scryfallId] = card_json_light
            self.prices_json = card_json_light
            # Save
            with open(self.cache_dir_meta+self.prices_json_file, 'w') as fp:
                json.dump(prices, fp, indent = 4)
        if self.foil: p = self.prices_json['usd_foil']
        else: p = self.prices_json['usd']
        if p is not None: self.price = float(p)
        else: self.price = 0.0
        return self.price

    def __apply_foil__(self, img):
        foil_layer = Image.open(self.res_dir+'foil_layer3.png')
        foil_layer = foil_layer.resize(img.size)
        foil_layer = foil_layer.convert("RGBA")
        foil_layer.putalpha(64)
        img = img.convert("RGBA")
        foil_image = Image.new("RGBA", img.size)
        foil_image = Image.alpha_composite(foil_image, img)
        foil_image = Image.alpha_composite(foil_image, foil_layer)
        return foil_image

    def __str__(self):
        ret = self.card_print_separator
        ret = ret + '\n[Name]\t\t' + self.name
        ret = ret + '\n[Set]\t\t' + self.set_code
        ret = ret + '\n[Rarity]\t' + self.rarity
        ret = ret + '\n[Foil]\t\t' + str(self.foil)
        ret = ret + '\n[Url]\t\t' + self.image_url
        ret = ret + '\n[Price]\t' + str(self.price)
        ret += '\n'
        ret += self.card_print_separator
        ret += '\n'
        return ret

    def __repr__(self):
        if self.foil: return '*'+self.name+'*'
        else: return self.name

    def display(self):
        self.__get_image__()
        print(self.__str__())
        self.image.show()

