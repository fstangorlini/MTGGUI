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

    def __init__(self,json_data:json, queue_:queue=None):
        self.image_resolution = 'normal' #small, normal, large, png, art_crop, or border_crop. Defaults to large.
        self.rarity_converter = {'mythic':'M','rare':'R','uncommon':'U','common':'C'}
        self.cache_dir_img = './cache/img/'
        self.file_extension = '.png'
        self.queue_ = queue_
        self.card_print_separator = '--------------------------------------------------'
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
            if self.queue_ is not None: self.queue_.put((0,'Image ['+self.name+'] not in cache. Fetching from '+self.image_url))
            try:
                img = Image.open(requests.get(self.image_url, stream=True).raw)
                img.save(self.cache_dir_img+self.uuid+self.file_extension)
                print('OK!')
                if self.queue_ is not None: self.queue_.put((0,'OK!'))
            except:
                print('NOK')
                if self.queue_ is not None: self.queue_.put((0,'Error downloading...'))
                img = Image.open('./res/mtg-card-back.png')
            self.image = img
            return img

    def __str__(self):
        ret = self.card_print_separator
        ret = ret + '\n[Name]\t\t' + self.name
        ret = ret + '\n[Set]\t\t' + self.set
        ret = ret + '\n[Rarity]\t' + self.rarity
        ret = ret + '\n[Url]\t\t' + self.image_url
        ret += '\n'
        ret += self.card_print_separator
        ret += '\n'
        return ret

    def __repr__(self):
        return self.name
