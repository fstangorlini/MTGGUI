from dataclasses import dataclass
import itertools
import json
from queue import Queue
import numpy as np
from PIL import Image
from MTGCard import MTGCard
import math
import os

@dataclass
class MTGCollection:

    card_list:list[MTGCard]
    page_image_list:list #images
    set_code:str
    queue_:Queue

    def __init__(self, set_code:str, queue_:Queue=None):
        self.set_code = set_code
        self.cards_in_page = 15
        self.card_dimensions = (488,680)
        self.cache_dir_meta = './cache/metadata/'
        self.boosters_json_file = 'boosters.json'
        self.cache_dir_collections = './cache/collections/'+self.set_code+'/'
        self.queue_ = queue_
        self.page_image_list = []

    def get_set_json(self):
        with open(self.cache_dir_meta+self.set_code+'.json', 'r', encoding='UTF-8') as file:
            set_json = json.loads(file.read())
        return set_json

    def get_booster_json(self):
        with open(self.cache_dir_meta+self.boosters_json_file, 'r') as file:
            boosters_json = json.loads(file.read())
        return boosters_json

    def get_collection(self, set_code:str, set_json:json):
        #loads booster json file
        boosters_json = self.get_booster_json()
        collection = {}
        #populate set data
        for card_json_data in set_json['data']['cards']:
            card = MTGCard(card_json_data, collected=False)
            collection[card_json_data['uuid']] = card

        #populate with collected cards
        for booster_json in boosters_json.values():
            if booster_json['setCode']==set_code:
                for card_data in booster_json['cards']:
                    if not collection[card_data['uuid']].foil:
                        collection[card_data['uuid']].collected = True
                        collection[card_data['uuid']].foil = card_data['foil']
        return collection

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

    def get_card_by_uuid(self, set_json_data:json, uuid:str):
        return MTGCard(list(filter(lambda card: (card['uuid'] == uuid), set_json_data['data']['cards']))[0])

    def __generate_page__(self, collection:json, page:int, set_json_data:json):
        msg = 'Generating page '+str(page)+'/'+str(math.ceil(len(collection)/self.cards_in_page))+'...'
        print(msg)
        if self.queue_ is not None: self.queue_.put((1,msg))
        #card_uuids = list(collection.keys())
        collection_data = dict(itertools.islice(collection.items(), (page-1)*self.cards_in_page, page*self.cards_in_page ))
        #card_uuids = card_uuids[(page-1)*page_size:page*page_size]
        card_image_list_as_image = []
        card_back_img = Image.open('./res/mtg-card-back.png').resize(self.card_dimensions).convert("RGB")
        for uuid, card in collection_data.items():
            if card.collected:
                if card.foil: card.foil = True
                img = card.__get_image__().convert("RGB")
                if img.size != self.card_dimensions: img = img.resize(self.card_dimensions)
                card_image_list_as_image.append(img)
            else:
                card_image_list_as_image.append(card_back_img)
        for i in range(self.cards_in_page-len(card_image_list_as_image)): card_image_list_as_image.append(card_back_img)
        page_img = self.__assemble__(card_image_list_as_image)
        page_img = page_img.resize((1100,900))
        return page_img

    def __generate_collection_book__(self, collection:json, set_json_data:json):
        collection_size = len(collection)
        number_of_pages = math.ceil(collection_size/self.cards_in_page)
        msg = 'Generating Collection Book.\nCards: '+str(collection_size)+'\nPages:' +str(number_of_pages)
        print(msg)
        if self.queue_ is not None: self.queue_.put((1,msg))
        if not os.path.isdir(self.cache_dir_collections): os.makedirs(self.cache_dir_collections)
        for page_no in range(1,number_of_pages+1):
            page_img = self.__generate_page__(collection, page_no, set_json_data)
            self.page_image_list.append(page_img)
            #save
            #file_name = self.cache_dir_collections+self.set_code+'_'+str(page_no)+'.png'
            #page_img.save(file_name)
        # opening first page to browse collection
        #TODO
        #?????
        #print(f'Done generating Collection Book. Please check {self.cache_dir_collections} folder for images.')
        return self.page_image_list

