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
from tkinter.font import BOLD
from PIL import Image, ImageTk
from MTGJson import MTGJson
from MTGCard import MTGCard
from MTGCollection import MTGCollection

######################################################################################################
# Classes

# Threaded task to handle image download and
# booster generation without freezing up UI
class ThreadedTask(threading.Thread):

    def __init__(self, queue_:queue, set_code:str):
        threading.Thread.__init__(self)
        self.queue_ = queue_
        self.set_code = set_code
        
    def run(self):
        c = MTGCollection(self.set_code, self.queue_)
        set_json = c.get_set_json()
        collection = c.get_collection(self.set_code, set_json)
        collection_book_images = c.__generate_collection_book__(collection, set_json)
        if collection_book_images is not None: self.queue_.put((2,(collection, c.page_image_list)))
        else: self.queue_.put((1,'Error viewing Collection. Please try again.'))

######################################################################################################
# GUI
class MTGCollectionsGUI(tk.Frame):
    
    queue_:queue
    
    def __init__(self, queue_):
        #######################################################################
        # Variables
        self.queue_ = queue_
        self.root = Toplevel()
        super().__init__(self.root)
        self.pack()
        self.images = []
        self.TITLE = 'Magic the Gathering - Collection'
        self.SUBTITLE = self.TITLE
        self.SETS = ['10E', '2ED', '2X2', '2XM', '30A', '3ED', '40K', '4BB', '4ED', '5DN', '5ED', '6ED', '7ED', 
                     '8ED', '9ED', 'A25', 'AAFR', 'ABRO', 'ACLB', 'ADMU', 'AER', 'AFC', 'AFR', 'AJMP', 'AKH', 'AKHM', 
                     'AKR', 'ALA', 'ALL', 'ALTR', 'AMH1', 'AMH2', 'AMID', 'AMOM', 'ANA', 'ANB', 'ANEO', 'AONE', 
                     'APC', 'ARB', 'ARC', 'ARN', 'ASNC', 'ASTX', 'ATH', 'ATQ', 'AVOW', 'AVR', 'AZNR', 'BBD', 
                     'BCHR', 'BFZ', 'BNG', 'BOK', 'boosters', 'BOT', 'BRB', 'BRC', 'BRO', 'BRR', 'BTD', 'C13', 
                     'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21', 'CC1', 'CC2', 'CED', 'CEI', 'CHK', 
                     'CHR', 'CLB', 'CM1', 'CM2', 'CMA', 'CMB1', 'CMB2', 'CMD', 'CMM', 'CMR', 'CN2', 'CNS', 'CON_', 
                     'CP1', 'CP2', 'CP3', 'CSP', 'CST', 'DBL', 'DD1', 'DD2', 'DDC', 'DDD', 'DDE', 'DDF', 'DDG', 
                     'DDH', 'DDI', 'DDJ', 'DDK', 'DDL', 'DDM', 'DDN', 'DDO', 'DDP', 'DDQ', 'DDR', 'DDS', 'DDT', 
                     'DDU', 'DGM', 'DIS', 'DKA', 'DKM', 'DMC', 'DMR', 'DMU', 'DOM', 'DPA', 'DRB', 'DRK', 'DST', 
                     'DTK', 'DVD', 'E01', 'E02', 'EA1', 'EA2', 'ELD', 'EMA', 'EMN', 'EVE', 'EVG', 'EXO', 'EXP', 
                     'F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 
                     'F14', 'F15', 'F16', 'F17', 'F18', 'FBB', 'FBRO', 'FDMU', 'FEM', 'FJ22', 'FJMP', 'FMB1', 'FMOM', 
                     'FNM', 'FONE', 'FRF', 'FUT', 'G00', 'G01', 'G02', 'G03', 'G04', 'G05', 'G06', 'G07', 'G08', 'G09', 
                     'G10', 'G11', 'G17', 'G18', 'G99', 'GDY', 'GK1', 'GK2', 'GN2', 'GN3', 'GNT', 'GPT', 'GRN', 'GS1', 
                     'GTC', 'GVL', 'H09', 'H17', 'H1R', 'HA1', 'HA2', 'HA3', 'HA4', 'HA5', 'HA6', 'HBG', 'HHO', 'HML', 
                     'HOP', 'HOU', 'HTR16', 'HTR17', 'HTR18', 'HTR19', 'HTR20', 'ICE', 'IKO', 'IMA', 'INV', 'ISD', 'ITP', 
                     'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18', 'J19', 'J20', 'J21', 'J22', 'JGP', 'JMP', 'JOU', 
                     'JUD', 'JVC', 'KHC', 'KHM', 'KLD', 'KLR', 'KTK', 'L12', 'L13', 'L14', 'L15', 'L16', 'L17', 'LEA', 
                     'LEB', 'LEG', 'LGN', 'LRW', 'LTC', 'LTR', 'M10', 'M11', 'M12', 'M13', 'M14', 'M15', 'M19', 'M20', 
                     'M21', 'MAFR', 'MAT', 'MB1', 'MBRO', 'MBS', 'MCLB', 'MD1', 'MDMU', 'ME1', 'ME2', 'ME3', 'ME4', 
                     'MED', 'MGB', 'MH1', 'MH2', 'MIC', 'MID', 'MIR', 'MKHM', 'MM2', 'MM3', 'MMA', 'MMH2', 'MMID', 
                     'MMQ', 'MNEO', 'MOC', 'MOM', 'MONE', 'MOR', 'MP2', 'MPR', 'MPS', 'MRD', 'MSNC', 'MSTX', 'MUL', 
                     'MVOW', 'MZNR', 'NCC', 'NEC', 'NEM', 'NEO', 'NPH', 'O90P', 'OAFC', 'OANA', 'OARC', 'OC13', 'OC14', 
                     'OC15', 'OC16', 'OC17', 'OC18', 'OC19', 'OC20', 'OC21', 'OCM1', 'OCMD', 'ODY', 'OE01', 'OGW', 
                     'OHOP', 'OLEP', 'OLGC', 'OMIC', 'ONC', 'ONE', 'ONS', 'OPC2', 'OPCA', 'ORI', 'OVNT', 'OVOC', 'P02', 
                     'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P10E', 'P11', 'P15A', 'P22', 'P23', 
                     'P2HG', 'P30A', 'P30H', 'P5DN', 'P8ED', 'P9ED', 'PAER', 'PAFR', 'PAKH', 'PAL00', 'PAL01', 'PAL02', 
                     'PAL03', 'PAL04', 'PAL05', 'PAL06', 'PAL99', 'PALA', 'PALP', 'PANA', 'PAPC', 'PARB', 'PARC', 
                     'PARL', 'PAST', 'PAVR', 'PBBD', 'PBFZ', 'PBNG', 'PBOK', 'PBOOK', 'PBRO', 'PC2', 'PCA', 'PCEL', 
                     'PCHK', 'PCLB', 'PCMD', 'PCMP', 'PCNS', 'PCON', 'PCSP', 'PCTB', 'PCY', 'PD2', 'PD3', 'PDCI', 
                     'PDGM', 'PDIS', 'PDKA', 'PDMU', 'PDOM', 'PDP10', 'PDP12', 'PDP13', 'PDP14', 'PDP15', 'PDRC', 
                     'PDST', 'PDTK', 'PDTP', 'PELD', 'PELP', 'PEMN', 'PEVE', 'PEWK', 'PEXO', 'PF19', 'PF20', 'PF21', 
                     'PF23', 'PFRF', 'PFUT', 'PG07', 'PG08', 'PGPT', 'PGPX', 'PGRN', 'PGRU', 'PGTC', 'PGTW', 'PH17', 
                     'PH18', 'PH19', 'PH20', 'PH21', 'PHED', 'PHEL', 'PHJ', 'PHOP', 'PHOU', 'PHPR', 'PHTR', 'PHUK', 
                     'PI13', 'PI14', 'PIDW', 'PIKO', 'PINV', 'PISD', 'PJ21', 'PJAS', 'PJJT', 'PJOU', 'PJSE', 'PJUD', 
                     'PKHM', 'PKLD', 'PKTK', 'PL21', 'PL22', 'PL23', 'PLC', 'PLG20', 'PLG21', 'PLG22', 'PLGM', 'PLGN', 
                     'PLIST', 'PLNY', 'PLRW', 'PLS', 'PM10', 'PM11', 'PM12', 'PM13', 'PM14', 'PM15', 'PM19', 'PM20', 
                     'PM21', 'PMBS', 'PMEI', 'PMH1', 'PMH2', 'PMIC', 'PMID', 'PMMQ', 'PMOA', 'PMOM', 'PMOR', 'PMPS', 
                     'PMPS06', 'PMPS07', 'PMPS08', 'PMPS09', 'PMPS10', 'PMPS11', 'PMRD', 'PNAT', 'PNCC', 'PNEM', 'PNEO', 
                     'PNPH', 'PODY', 'POGW', 'PONE', 'PONS', 'POR', 'PORI', 'PPC1', 'PPCY', 'PPLC', 'PPLS', 'PPP1', 
                     'PPRO', 'PPTK', 'PR2', 'PR23', 'PRAV', 'PRCQ', 'PRED', 'PRES', 'prices', 'PRIX', 'PRM', 'PRNA', 
                     'PROE', 'PRTR', 'PRW2', 'PRWK', 'PS11', 'PS14', 'PS15', 'PS16', 'PS17', 'PS18', 'PS19', 'PSAL', 
                     'PSCG', 'PSDC', 'PSDG', 'PSHM', 'PSNC', 'PSOI', 'PSOK', 'PSOM', 'PSS1', 'PSS2', 'PSS3', 'PSTH', 
                     'PSTX', 'PSUM', 'PSUS', 'PSVC', 'PTC', 'PTG', 'PTHB', 'PTHS', 'PTK', 'PTKDF', 'PTMP', 'PTOR', 
                     'PTSNC', 'PTSP', 'PUDS', 'PULG', 'PUMA', 'PUNH', 'PURL', 'PUSG', 'PUST', 'PVAN', 'PVOW', 'PW09', 
                     'PW10', 'PW11', 'PW12', 'PW21', 'PW22', 'PW23', 'PWAR', 'PWCS', 'PWOR', 'PWOS', 'PWPN', 'PWWK', 
                     'PXLN', 'PXTC', 'PZ1', 'PZ2', 'PZEN', 'PZNR', 'Q06', 'Q07', 'Q08', 'RAV', 'REN', 'RIN', 'RIX', 'RNA', 
                     'ROE', 'RQS', 'RTR', 'S00', 'S99', 'SBRO', 'SCD', 'SCG', 'SCH', 'SHM', 'SIR', 'SIS', 'SKHM', 'SLC', 
                     'SLD', 'SLP', 'SLU', 'SLX', 'SMID', 'SMOM', 'SNC', 'SNEO', 'SOI', 'SOK', 'SOM', 'SS1', 'SS2', 'SS3', 
                     'SSTX', 'STA', 'STH', 'STX', 'SUM', 'SUNF', 'SVOW', 'SZNR', 'TBTH', 'TD0', 'TD2', 'TDAG', 'TFTH', 
                     'THB', 'THP1', 'THP2', 'THP3', 'THS', 'TMP', 'TOR', 'TPR', 'TSB', 'TSP', 'TSR', 'UDS', 'UGIN', 'UGL', 
                     'ULG', 'UMA', 'UND', 'UNF', 'UNH', 'UPLIST', 'USG', 'UST', 'V09', 'V10', 'V11', 'V12', 'V13', 'V14', 
                     'V15', 'V16', 'V17', 'VIS', 'VMA', 'VOC', 'VOW', 'W16', 'W17', 'WAR', 'WC00', 'WC01', 'WC02', 'WC03', 
                     'WC04', 'WC97', 'WC98', 'WC99', 'WDMU', 'WHO', 'WMC', 'WMOM', 'WONE', 'WTH', 'WWK', 'XANA', 'XLN', 
                     'YBRO', 'YDMU', 'YMID', 'YNEO', 'YONE', 'YSNC', 'ZEN', 'ZNC', 'ZNE', 'ZNR']
        self.display_index = 0
        self.done_processing = False
        self.__custom_init__()
        self.__align_elements__()
        self.__post_init__()
    
    def __disable_buttons__(self):
        self.button_generate.config(state='disabled')
        self.button_next.config(state='disabled')
        self.button_prev.config(state='disabled')
    
    def __enable_buttons__(self):
        self.button_generate.config(state='normal')
        self.button_next.config(state='normal')
        self.button_prev.config(state='normal')
    
    def __action_button_generate__(self):
        selected_set = self.stringvar_sets.get()
        if selected_set in self.SETS:
            self.done_processing = False
            self.images.clear()
            self.display_index = 0
            self.__disable_buttons__()
            self.progress_bar.start()
            ThreadedTask(self.queue_,selected_set).start()
        else:
            self.__put_text_in_status__('Error checking for collection. Ensure the set code is valid and try again.')

    def __action_button_next__(self):
        if self.display_index < len(self.collection_book_images):
            self.display_index+=1
            img = self.collection_book_images[self.display_index]
            self.__update_image__(self.label_img, img)
    
    def __action_button_prev__(self):
        if self.display_index > 0:
            self.display_index-=1
            img = self.collection_book_images[self.display_index]
            self.__update_image__(self.label_img, img)

    # updates an image into UI Label
    def __update_image__(self, label:Label, image:Image):
        img = ImageTk.PhotoImage(image)
        label.configure(image = img)
        label.image = img

    # puts text into status text field at the bottom
    def __put_text_in_status__(self, text:str):
        self.textfield_status.config(state='normal')
        self.textfield_status.delete(0,END)
        self.textfield_status.insert(0,text)
        self.textfield_status.config(state='disabled')

    def __done_processing__(self, collection:dict, collection_book_images:list):
        self.done_processing = True
        img = collection_book_images[self.display_index]
        self.__update_image__(self.label_img, img)
        #TODO
        total_worth = 0.0
        for card in collection.values():
            if card.collected:
                total_worth+=card.__get_price__()
        msg = 'Total collection worth: $ '+str("{:.2f}".format(total_worth))
        print(msg)
        self.queue_.put((1,msg))

    # process messages on queue (shared with other classes)
    def __process_queue__(self):
        msg = None
        if(self.queue_.empty()==False):
            msg = self.queue_.get(0)
            #msg[0]==1 only when info/error msg is passed
            if(msg[0]==1):
                self.progress_bar.stop()
                self.__enable_buttons__()
            #msg[0]==2 only when booster is generated successfully
            if(msg[0]==2):
                self.collection = msg[1][0]
                self.collection_book_images = msg[1][1]
                self.__done_processing__(self.collection, self.collection_book_images)
        return msg
    
    # runs every 100ms to update UI elements
    def __update_root__(self):
        self.root.after(100, self.__update_root__)
        if(self.queue_.empty()==False):
            msg = self.__process_queue__()
            if(msg[0]!=2): self.__put_text_in_status__(msg[1])
    
    def __custom_init__(self):
        #######################################################################
        # Define root window properties
        self.root.title(self.TITLE)
        self.root.resizable(False, False)
        #self.root.geometry('1920x1000')
        self.root.state('zoomed')
        #self.root.configure(bg='black')
        #self.root.title("wm min/max")
        
        #######################################################################
        # Create elements        
        self.stringvar_text_status  = StringVar()
        self.stringvar_sets         = StringVar()
        self.label_subtitle         = Label(self.root,text=self.SUBTITLE,font=("Segoe UI", 16, BOLD))
        self.textfield_status       = Entry(self.root,width=320,textvariable=self.stringvar_text_status)
        self.progress_bar           = ttk.Progressbar(orient="horizontal",length=320, mode="determinate")
        self.label_set_code         = Label(self.root,text='Set code',width=8,font=("Segoe UI", 10))
        self.label_img              = Label(self.root)
        self.entry_sets             = Entry(self.root,width=8,textvariable=self.stringvar_sets)
        self.button_generate        = Button(self.root,text='View Collection',command=self.__action_button_generate__, width=16)
        self.button_next            = Button(self.root,text='>',command=self.__action_button_next__, width=1)
        self.button_prev            = Button(self.root,text='<',command=self.__action_button_prev__, width=1)
        
    def __align_elements__(self):
        #######################################################################
        # Align elements to grid
        self.label_subtitle.place(x=750,y=0)
        self.label_set_code.place(x=780,y=40)
        self.entry_sets.place(x=850,y=43)
        self.button_generate.place(x=930,y=40)
        self.progress_bar.place(x=0,y=1017)
        self.textfield_status.place(x=0,y=1037)
        self.label_img.place(x=380,y=100)
        self.button_next.place(x=1900,y=500)
        self.button_prev.place(x=5,y=500)
        self.progress_bar.start()

    def __post_init__(self):
        #######################################################################
        # Post
        self.__put_text_in_status__('Please inform Set code and click View Collection button. (I.E. LEA = Legacy Alpha)')
        self.entry_sets.insert(0,'LEA')
        #self.button_next.config(state='disabled')
        #self.button_prev.config(state='disabled')
        self.root.after(100, self.__update_root__)
        self.root.mainloop()
       
# Initialize
if __name__ == "__main__":
    g = MTGCollectionsGUI(queue.Queue())
