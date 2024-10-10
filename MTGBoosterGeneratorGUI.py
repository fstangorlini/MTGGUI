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

######################################################################################################
# Classes

# Threaded task to handle image download and
# booster generation without freezing up UI
class ThreadedTask(threading.Thread):

    def __init__(self, queue_:queue, mtgjson:object, set_name:str, selected_booster_distribution:str):
        threading.Thread.__init__(self)
        self.queue_ = queue_
        self.set_name = set_name
        self.mtgjson = mtgjson
        self.selected_booster_distribution = selected_booster_distribution
        
    def run(self):
        booster = self.mtgjson.generate_booster(self.set_name, self.selected_booster_distribution)
        if booster is not None: self.queue_.put((2,booster))
        else: self.queue_.put((1,'Error generating booster. Ensure the set code is valid and try again.'))

######################################################################################################
# GUI
class MTGBoosterGeneratorGUI(tk.Frame):
    
    queue_:queue
    image_list:list
    mtgjson:MTGJson
    
    # generate button action
    def __action_button_generate__(self):
        selected_set = self.stringvar_sets.get()
        if selected_set in self.SETS:
            self.done_processing = False
            self.images.clear()
            self.display_index = 1
            self.__update_images__()
            self.__disable_buttons__()
            self.progress_bar.start()
            ThreadedTask(self.queue_,self.mtgjson,selected_set, self.combo_booster_distribution.get()).start()
        else:
            self.__put_text_in_status__('Error generating booster. Ensure the set code is valid and try again.')
    
    # next button action
    def __action_button_next__(self):
        if self.display_index >= self.booster_size: self.display_index = 0
        self.display_index+=1
        self.__update_images__()
        return
    
    # previous button action
    def __action_button_prev__(self):
        if self.display_index <= 1: self.display_index = self.booster_size+1
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
    
    # populates list of all images once. self.images is a list of images with tuple(small,large)
    def __populate_image_list__(self, booster:list[MTGCard]):
        self.images.append((self.img_card_back[0],self.img_card_back[1]))
        for card in booster:
            s = card.image.resize(self.corner_card_size)
            l = card.image.resize(self.centered_card_size)
            self.images.append((s,l))
        self.images.append((self.img_card_back[0],self.img_card_back[1]))
    
    # updates an image into UI Label
    def __update_image__(self, label:Label, image:Image):
        img = ImageTk.PhotoImage(image)
        label.configure(image = img)
        label.image = img

    # updates all images into UI labels (left, center, right)
    def __update_images__(self):
        if not self.done_processing:
            self.__update_image__(self.label_img_mid, self.img_card_back[1])
            self.__update_image__(self.label_img_left, self.img_card_back[0])
            self.__update_image__(self.label_img_right, self.img_card_back[0])
        else:
            self.__update_image__(self.label_img_mid, self.images[self.display_index][1])
            self.__update_image__(self.label_img_left, self.images[self.display_index-1][0])
            self.__update_image__(self.label_img_right, self.images[self.display_index+1][0])

    def __populate_booster_distributions__(self):
        booster_distributions = self.mtgjson.get_booster_distribution_values(self.stringvar_sets.get())
        self.combo_booster_distribution['values'] = [e for e in booster_distributions]
        self.combo_booster_distribution.current(0)

    # puts text into status text field at the bottom
    def __put_text_in_status__(self, text:str):
        self.textfield_status.config(state='normal')
        self.textfield_status.delete(0,END)
        self.textfield_status.insert(0,text)
        self.textfield_status.config(state='disabled')

    def __get_card_prices__(self, booster:list[MTGCard]):
        total_value = 0.0
        for card in booster:
            total_value += card.price
        return "{:.2f}".format(total_value)

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
                self.booster = msg[1]
                self.done_processing = True
                self.booster_size = len(self.booster)
                self.__populate_image_list__(self.booster)
                self.__update_images__()
                msg = 'Total booster worth: $ '+str(self.__get_card_prices__(self.booster))
                print(msg)
                self.queue_.put((1,msg))
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
        self.root.geometry(self.GEOMETRY)
        self.root.resizable(False, False)
        
        #######################################################################
        # Create elements        
        self.stringvar_text_status  = StringVar()
        self.stringvar_sets         = StringVar()
        self.label_subtitle         = Label(self.root,text=self.SUBTITLE,font=("Segoe UI", 16, BOLD))
        self.textfield_status       = Entry(self.root,width=105,textvariable=self.stringvar_text_status)
        #self.progress_label         = Label(self.root,text=self.label_progress,font=("Segoe UI", 10))
        self.progress_bar           = ttk.Progressbar(orient="horizontal",length=self.width, mode="determinate")
        self.label_set_code         = Label(self.root,text='Set code',width=8,font=("Segoe UI", 10))
        self.combo_booster_distribution_value = StringVar()
        self.combo_booster_distribution = ttk.Combobox(self.root, state="readonly", textvariable=self.combo_booster_distribution_value)
        self.combo_booster_distribution['values'] = ('None')
        self.combo_booster_distribution.current(0)
        self.label_img_mid          = Label(self.root)
        self.label_img_left         = Label(self.root)
        self.label_img_right        = Label(self.root)
        self.entry_sets             = Entry(self.root,width=8,textvariable=self.stringvar_sets, validate="focusout", validatecommand=self.__populate_booster_distributions__)
        self.button_generate        = Button(self.root,text='Generate',command=self.__action_button_generate__, width=16)
        self.button_next            = Button(self.root,text='Next',command=self.__action_button_next__, width=16)
        self.button_prev            = Button(self.root,text='Previous',command=self.__action_button_prev__, width=16)
        
    def __align_elements__(self):
        #######################################################################
        # Align elements to grid
        self.label_subtitle.place(x=110,y=10)
        self.label_set_code.place(x=40,y=57)
        self.entry_sets.place(x=110,y=60)
        self.combo_booster_distribution.place(x=180,y=60)
        self.button_generate.place(x=330,y=57)
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
        self.__put_text_in_status__('Please inform Set code and click Generate button. (I.E. LEA = Legacy Alpha)')
        self.entry_sets.insert(0,'LTR')
        self.button_next.config(state='disabled')
        self.button_prev.config(state='disabled')
        self.__update_images__()
        self.__populate_booster_distributions__()
        self.root.after(100, self.__update_root__)
        self.root.mainloop()

    def __init__(self, queue_):
        #######################################################################
        # Variables
        self.queue_ = queue_
        self.root = Toplevel()
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
        self.SETS = ['FFDN', 'FDN', 'ADSK', 'TDSK', 'DSC', 'DSK', 'TDSC', 'PDSK', 'YBLB', 'PLG24', 'TBLB', 'PBLB', 'TBLC', 'ABLB', 'MB2', 'PCBB', 'BLB', 'BLC', 'AACR', 'ACR','TACR','PMH3','SMH3','M3C','MH3','TMH3','TM3C','AMH3','H2R','YOTJ','POTJ','TOTJ','AOTJ','TOTP','OTJ','BIG','OTC','TOTC','OTP','TBIG','PIP','TPIP','YMKM','FCLU','CLU','PSS4','TMKC','PMKM','TMKM','AMKM','MKC','MKM','WMKM','PL24','RVR','TRVR','PW24','PF24','YLCI','SPG','PLCI','ALCI','TLCC','TREX','REX','LCI','TLCI','PMAT','SLCI','LCC','TWHO','WHO','YWOE','PWOE','WOC','WOT','TWOC','TWOE','WWOE','AWOE','PMDA','PTSR','WOE','P30T','ACMM','TCMM','CMM','PH22','HA7','EA3','PF23','PLTR','LTC','TLTR','ALTR','LTR','TLTC','FLTR','MAT','FMOM','TMOC','PMOM','TMOM','AMOM','SMOM','TMUL','MOC','WMOM','MOM','MUL','SIS','SIR','YONE','SLP','DA1','PL23','PONE','TONE','TONC','ONE','FONE','ONC','AONE','MONE','WONE','DMR','TDMR','PR23','P23','PW23','YBRO','EA2','TSCD','SCD','FJ22','J22','30A','T30A','PEWK','BRC','BRR','PBRO','TBOT','BOT','PTBRO','BRO','SBRO','MBRO','TBRC','TBRO','FBRO','ABRO','SLC','TGN3','GN3','ULST','UNF','TUNF','SUNF','40K','T40K','YDMU','PRCQ','P30H','PDMU','PTDMU','FDMU','ADMU','DMC','TDMC','DMU','TDMU','WDMU','MDMU','P30M','P30A','PH21','PSVC','EA1','HA6','SCH','2X2','T2X2','HBG','PLG22','PCLB','MCLB','TCLB','CLB','ACLB','YSNC','PTSNC','PNCC','TSNC','SNC','NCC','PSNC','MSNC','ASNC','TNCC','GDY','Q07','YNEO','PW22','SLX','PL22','PNEO','MNEO','SNEO','TNEO','TNEC','NEO','NEC','ANEO','CC2','DBL','P22','YMID','PVOW','TVOW','TVOC','OVOC','MVOW','SVOW','AVOW','VOC','VOW','Q06','SMID','AMID','MIC','TMIC','TMID','PMID','OMIC','MMID','MID','J21','CMB2','PH20','PAFR','OAFC','AAFR','AFC','TAFC','TAFR','MAFR','AFR','PLG21','TMH2','AMH2','PMH2','MMH2','MH2','PW21','H1R','HA5','PSTX','TSTX','TC21','SSTX','MSTX','STA','C21','ASTX','OC21','STX','TTSR','TSR','HA4','PKHM','MKHM','SKHM','KHM','AKHM','TKHC','TKHM','KHC','PL21','PJ21','CC1','TCMR','PCMR','CMR','KLR','PLST','PZNR','TZNC','MZNR','ZNR','AZNR','SZNR','ZNE','ZNC','TZNR','AKR','ANB','2XM','T2XM','PH19','AJMP','JMP','PM21','TM21','M21','SS3','FJMP','SLU','HA3','PLG20','PIKO','IKO','TIKO','OC20','C20','TC20','HA2','TUND','UND','PTHB','TTHB','THB','PF20','J20','SLD','HA1','TGN2','GN2','CMB1','PTG','PELD','ELD','PWCS','TELD','OC19','C19','TC19','PH18','PS19','PPP1','PM20','TM20','M20','SS2','PMH1','MH1','AMH1','TMH1','PWAR','TWAR','WAR','J19','PRW2','GK2','TGK2','PRNA','RNA','TRNA','PF19','OPCA','PUMA','TUMA','UMA','GNT','G18','PRWK','TGK1','GK1','PGRN','TGRN','GRN','MED','TMED','OC18','C18','TC18','PH17','PS18','XANA','ANA','PANA','OANA','PM19','TM19','M19','PSS3','GS1','SS1','PBBD','TBBD','BBD','CM2','TCM2','PDOM','TDOM','DOM','DDU','TDDU','A25','TA25','PLNY','PNAT','TRIX','PRIX','RIX','J18','F18','PUST','TUST','UST','TIMA','PXTC','V17','E02','IMA','DDT','TDDT','G17','PXLN','XLN','TXLN','PSS2','H17','PHTR','TE01','OC17','TC17','C17','PS17','PHOU','HOU','THOU','OE01','E01','TCMA','CMA','PAKH','AKH','TAKH','MP2','W17','DDS','TDDS','TMM3','MM3','PAER','TAER','AER','L17','F17','J17','PCA','TPCA','PZ2','OC16','C16','TC16','PS16','PKLD','KLD','TKLD','MPS','DDR','CN2','TCN2','V16','PEMN','EMN','TEMN','EMA','TEMA','PSOI','TSOI','SOI','W16','DDQ','OGW','TOGW','POGW','L16','J16','F16','PZ1','TC15','C15','OC15','PBFZ','TBFZ','BFZ','PSS1','EXP','DDP','V15','CP3','PORI','ORI','TORI','PS15','MM2','TMM2','TPR','PTKDF','PDTK','DTK','TDTK','DDO','PFRF','CP2','TFRF','FRF','UGIN','L15','F15','J15','TJVC','TDVD','TGVL','GVL','EVG','TEVG','JVC','DVD','OC14','C14','TC14','PKTK','TKTK','KTK','DDN','V14','TM15','CP1','M15','PM15','PPC1','PDP15','PS14','VMA','PCNS','TCNS','CNS','TMD1','MD1','TDAG','THP3','TJOU','JOU','PJOU','TDDM','DDM','TBTH','BNG','THP2','TBNG','PBNG','L14','J14','F14','OC13','C13','TFTH','THS','THP1','TTHS','PTHS','TDDL','DDL','V13','M14','TM14','PM14','PSDC','TMMA','MMA','DGM','TDGM','PDGM','WMC','TDDK','DDK','GTC','TGTC','PGTC','PDP14','L13','F13','J13','OCM1','CM1','RTR','PRTR','TRTR','DDJ','TDDJ','V12','M13','TM13','PM13','OPC2','PC2','AVR','TAVR','PHEL','PAVR','DDI','TDDI','DKA','TDKA','PDKA','PW12','PDP13','PIDW','L12','J12','F12','PD3','ISD','TISD','PISD','TDDH','DDH','V11','TM12','M12','PM12','OCMD','PCMD','CMD','TD2','TNPH','NPH','PNPH','DDG','TDDG','MBS','TMBS','PMBS','ME4','PMPS11','PDP12','PW11','OLGC','PS11','P11','G11','F11','PD2','TD0','SOM','TSOM','PSOM','TDDF','DDF','V10','M11','TM11','PM11','OARC','ARC','DPA','PROE','TROE','ROE','TDDE','DDE','PWWK','WWK','TWWK','PDP10','PMPS10','P10','F10','G10','H09','DDD','TDDD','PZEN','TZEN','ZEN','ME3','OHOP','HOP','PHOP','V09','TM10','M10','PM10','PARB','TARB','ARB','TDDC','DDC','PURL','PCON','TCON','CON','PBOOK','PDTP','PMPS09','F09','G09','P09','TDD2','DD2','PALA','ALA','TALA','ME2','DRB','PEVE','EVE','TEVE','PSHM','TSHM','SHM','P15A','PMOR','MOR','TMOR','PMPS08','P08','G08','F08','DD1','TDD1','PLRW','LRW','TLRW','ME1','10E','P10E','T10E','PFUT','FUT','PGPX','PPRO','PPLC','PLC','PRES','PMPS07','F07','P07','G07','HHO','PTSP','TSB','TSP','PCSP','CST','CSP','PDIS','DIS','PCMP','PGPT','GPT','PAL06','PMPS06','PJAS','P06','G06','F06','PDCI','PHUK','P2HG','PRAV','RAV','PSAL','P9ED','9ED','PSOK','SOK','PBOK','BOK','PMPS','PAL05','PJSE','G05','F05','P05','PUNH','UNH','PCHK','CHK','WC04','PMRD','P5DN','5DN','PDST','DST','PAL04','F04','G04','P04','MRD','WC03','P8ED','8ED','PSCG','SCG','PLGN','LGN','PMOA','PJJT','PAL03','F03','P03','G03','OVNT','ONS','PONS','WC02','PHJ','PRM','PJUD','JUD','PTOR','TOR','PAL02','PR2','G02','F02','DKM','PODY','ODY','WC01','PSDG','PAPC','APC','7ED','PPLS','PLS','PAL01','MPR','F01','G01','PINV','INV','BTD','WC00','PPCY','PCY','S00','PNEM','NEM','PELP','PAL00','G00','FNM','PSUS','BRB','PMMQ','MMQ','PWOS','PWOR','WC99','PGRU','S99','PUDS','UDS','PPTK','PTK','6ED','PULG','ULG','PAL99','G99','ATH','PUSG','USG','PALP','WC98','TUGL','UGL','P02','PEXO','EXO','PSTH','STH','JGP','PTMP','TMP','WC97','WTH','OLEP','POR','PVAN','PMIC','PAST','5ED','VIS','ITP','MGB','MIR','PRED','PCEL','PARL','RQS','PLGM','ALL','PTC','O90P','HML','REN','RIN','CHR','BCHR','ICE','4BB','4ED','PMEI','FEM','PHPR','DRK','PDRC','SUM','LEG','3ED','FBB','ATQ','ARN','CEI','CED','2ED','LEB','LEA']
        self.label_progress = 'Progress'
        self.img_card_back = Image.open('./res/mtg-card-back.png')
        self.img_card_back = (self.img_card_back.resize(self.corner_card_size),self.img_card_back.resize(self.centered_card_size))
        self.display_index = 1
        self.done_processing = False
        self.mtgjson = MTGJson(self.queue_)
        self.__custom_init__()
        self.__align_elements__()
        self.__post_init__()
       
# Initialize
if __name__ == "__main__":
    g = MTGBoosterGeneratorGUI(queue.Queue())
