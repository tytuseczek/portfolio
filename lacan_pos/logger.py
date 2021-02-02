# -*- coding: utf-8 -*-

from time import gmtime, strftime

class logger:
    
    def __init__(self, error_msg=False, info_msg=False): # 0 = "Error", 1 = "Info"
        t = strftime("%d %b %Y", gmtime())
        
        self.filename_error = "lacan_pos_%s_error.txt"%(t)
        self.filename_info = "lacan_pos_%s_info.txt"%(t)
        
        self(error_msg, info_msg)
    
    def __call__(self, error_msg=False, info_msg=False): # 0 = "Error", 1 = "Info"                
        t = strftime("%d %b %Y %H_%M_%S", gmtime())
        
        if error_msg:
            fe = open(self.filename_error, 'a')
            fe.write( "ERROR: %s %s\n"%(t, error_msg) )
            fe.close()
        if info_msg:
            fi = open(self.filename_info, 'a')
            fi.write( "INFO: %s %s\n"%(t, info_msg) )
            fi.close()