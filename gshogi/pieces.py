#
#   pieces.py
#
#   This file is part of gshogi   
#
#   gshogi is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   gshogi is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with gshogi.  If not, see <http://www.gnu.org/licenses/>.
#   

import gtk
import os
import traceback
from constants import *


class Pieces:
  

    def __init__(self):
        self.pieceset = 'eastern'     # eastern, western or custom        
        self.scale_factor = 1.0        
        self.prefix = None
        self.custom_piece_pixbuf = None
        self.custom_piece_path = None

        # create pixbuf for empty square
        self.pb_empty = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 64, 64)       
        self.pb_empty.fill(0xffffff00) # fill with transparent white
        

    def get_piece_default_colours(self):

        # (255, 255, 255, 0)   - white transaparent background
        # (0, 0, 0, 255)       - black edges
        # (255, 255, 215, 255) - cream fill
        # (0, 0, 1, 255)       - kanji 

        # Piece Colours
        # These default colours must match the colours of the PNG piece images on disk
        # Don't change these unless you change the images as well.        
        fill_colour = (255, 255, 215, 255)
        outline_colour = (0, 0, 0, 255)
        kanji_colour = (0, 0, 1, 255)

        return fill_colour, outline_colour, kanji_colour 


    # called from this module and from board.py init_board function
    def load_pieces(self, prefix):
        
        #  0 - unoccupied        
        #  1 - black pawn        
        #  2 - black lance        
        #  3 - black knight        
        #  4 - black silver general       
        #  5 - black gold general        
        #  6 - black bishop       
        #  7 - black rook       
        #  8 - black king
        #  9 - promoted black pawn       
        # 10 - promoted black lance        
        # 11 - promoted black knight       
        # 12 - promoted black silver general        
        # 13 - promoted black bishop       
        # 14 - promoted black rook
        # 15 - white pawn        
        # 16 - white lance        
        # 17 - white knight       
        # 18 - white silver general       
        # 19 - white gold general       
        # 20 - white bishop       
        # 21 - white rook        
        # 22 - white king        
        # 23 - promoted white pawn        
        # 24 - promoted white lance       
        # 25 - promoted white knight       
        # 26 - promoted white silver general       
        # 27 - promoted white bishop       
        # 28 - promoted white rook        
        
        if self.prefix is None:
            self.prefix = prefix
 
        self.piece_pixbuf, errmsg = self.load_pixbufs('eastern', prefix)
        self.western_piece_pixbuf, errmsg = self.load_pixbufs('western', prefix)
        self.piece_fill_colour, self.piece_outline_colour, self.piece_kanji_colour = self.get_piece_default_colours()
        if self.custom_piece_path is not None:
            self.custom_piece_pixbuf, errmsg = self.load_custom_pixbufs(self.custom_piece_path)
            # if pieces set to custom and they cannot be loaded then switch to eastern
            if self.custom_piece_pixbuf is None:
                if errmsg is not None:
                    print errmsg
                if self.pieceset == 'custom':                   
                    self.pieceset = 'eastern'

        
    def custom_pieces_loaded(self):
        if self.custom_piece_pixbuf is not None:
            return True
        else:
            return False


    # function to load images of the builtin pieces
    def load_pixbufs(self, piece_set, prefix):
        images = ['pawnB', 'lanceB', 'knightB', 'silverB', 'goldB', \
                  'bishopB', 'rookB', 'kingB', 'pawnPB', 'lancePB', \
                  'knightPB', 'silverPB', 'bishopPB', 'rookPB',     \
                  'pawnW', 'lanceW', 'knightW', 'silverW', 'goldW', \
                  'bishopW', 'rookW', 'kingW', 'pawnPW', 'lancePW', \
                  'knightPW', 'silverPW', 'bishopPW', 'rookPW'      \
                 ]        

        piece_pixbuf = []
        piece_pixbuf.append(self.pb_empty.copy()) # first pixbuf in list is empty square       

        for image in images:           
            image = 'images/' + piece_set + '/' + image + '.png'            
            piece_pixbuf.append(gtk.gdk.pixbuf_new_from_file(os.path.join(prefix, image)))

        return piece_pixbuf, None


    # function to load images of custom pieces provided by the user
    def load_custom_pixbufs(self, custom_path):
        images = ['pawnB', 'lanceB', 'knightB', 'silverB', 'goldB', \
                  'bishopB', 'rookB', 'kingB', 'pawnPB', 'lancePB', \
                  'knightPB', 'silverPB', 'bishopPB', 'rookPB'      \
                 ]

        #         'pawnW', 'lanceW', 'knightW', 'silverW', 'goldW', \
        #         'bishopW', 'rookW', 'kingW', 'pawnPW', 'lancePW', \
        #         'knightPW', 'silverPW', 'bishopPW', 'rookPW'      \
        #        ]        

        piece_pixbuf = []
        piece_pixbuf.append(self.pb_empty.copy()) # first pixbuf in list is empty square

        # if custom pieces get file extension (png or svg)        
        image = images[0]
        if os.path.isfile(os.path.join(custom_path, image + '.png')):                
            extension = '.png'
        elif os.path.isfile(os.path.join(custom_path, image + '.svg')):                 
            extension = '.svg'
        else:
           return None, 'Error loading custom pieces\n\nFile not found:pawnB.png or pawnB.svg'

        # Load black pieces
        for image in images:            
            # custom pieces
            image = image + extension
            path =  os.path.join(custom_path, image)
            if not os.path.isfile(path):                    
                errmsg = "Error loading custom pieces\nFile not found:" + image                   
                return None, errmsg                  
            pb = gtk.gdk.pixbuf_new_from_file(path)                
            piece_pixbuf.append(pb)                 
            #piece_pixbuf.append(gtk.gdk.pixbuf_new_from_file(os.path.join(custom_path, image))) 

        # Load white pieces
        for image in images:            
            image_white = image[0 : len(image) - 1] + 'W'   # change filename from pawnB to pawnW etc
            
            # if user has provided an image for white then use it
            image_white = image_white + extension
            path =  os.path.join(custom_path, image_white)
            if os.path.isfile(path):
                pb = gtk.gdk.pixbuf_new_from_file(path)                
                piece_pixbuf.append(pb)
                continue

            # no image provided for white so use the image for black and rotate it through 180 degrees           
            image = image + extension
            path =  os.path.join(custom_path, image)
                             
            pb = gtk.gdk.pixbuf_new_from_file(path)
            pb = pb.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
            piece_pixbuf.append(pb)            

        return piece_pixbuf, None


    # called from set_board_colours.py when user loads new custom pieces
    def load_custom_pieces(self, path):        
        custom_piece_pixbufs, errmsg = self.load_custom_pixbufs(path)
        # if no errors then set custom pixbufs to the new set
        if errmsg is None:
            self.custom_piece_pixbuf = custom_piece_pixbufs
            self.custom_piece_path = path 
        return errmsg


    # convert e.g. '#FFFFFF' into (255, 255, 255, 255)
    def convert_RGB(self, hexstring): 
        #e.g. #FF0000 for red
        r = hexstring[1:3] 
        g = hexstring[3:5]
        b = hexstring[5:7]        

        r_int = int(r, 16)
        g_int = int(g, 16)
        b_int = int(b, 16)
        a_int = 255 
       
        return (r_int, g_int, b_int, a_int)


    def change_piece_colours2(self, fill_colour, outline_colour, kanji_colour):       

        # colours are in a hexstring format #RRGGBB - convert them to an RGBA tuple
        fill_colour = self.convert_RGB(fill_colour)
        outline_colour = self.convert_RGB(outline_colour)
        kanji_colour = self.convert_RGB(kanji_colour)

        if self.piece_fill_colour == fill_colour and self.piece_outline_colour == outline_colour and self.piece_kanji_colour == kanji_colour:            
            return       

        self.load_pieces(self.prefix)

        self.piece_pixbuf = self.change_piece_colours(self.piece_pixbuf, fill_colour, outline_colour, kanji_colour)
        self.western_piece_pixbuf = self.change_piece_colours(self.western_piece_pixbuf, fill_colour, outline_colour, kanji_colour)

        self.piece_fill_colour = fill_colour
        self.piece_outline_colour = outline_colour
        self.piece_kanji_colour = kanji_colour


    def change_piece_colours(self, pixbuf, fill_colour, outline_colour, kanji_colour):        
        for i in range(1, len(pixbuf)):

            pb = pixbuf[i]          
   
            # Check the pixbuf is OK before changing the colours
            # should be no problem unless user has changed the image files
            colorspace = pb.get_colorspace()  
            if (colorspace != gtk.gdk.COLORSPACE_RGB):
                print "Warning - colorspace is not RGB in piece image. Setting piece colour may fail (in pieces.py)"
           
            nchannels = pb.get_n_channels()
            if (nchannels != 4):
                print "Warning - no of channels is not 4 in piece image (image not RGBA?). Setting piece colour may fail (in pieces.py)"               

            has_alpha = pb.get_has_alpha()
            if (not has_alpha):
                print "Warning - No alpha channel in piece image (image not RGBA?). Setting piece colour may fail (in pieces.py)" 

            bits_per_sample = pb.get_bits_per_sample()
            if (bits_per_sample != 8):
                print "Warning - Bits per color sample is not 8 in image. Setting piece colour may fail (in pieces.py)"                      

            newstr = ""            
            pixels_changed = 0

            px = pixbuf[i].get_pixels()

            # (255, 255, 255, 0)   - white transaparent background
            # (0, 0, 0, 255)       - black edges
            # (255, 255, 215, 255) - cream fill
            # (0, 0, 1, 255)       - kanji 

            for j in range (0, len(px), 4):
                r, g, b, a = ord(px[j]), ord(px[j + 1]), ord(px[j + 2]), ord(px[j + 3]) 
                if (r, g, b, a) == self.piece_fill_colour:
                    #
                    # Change the piece fill colour
                    # to what the user selected
                    #
                    newstr += chr(fill_colour[0])  # r
                    newstr += chr(fill_colour[1])  # g
                    newstr += chr(fill_colour[2])  # b
                    newstr += chr(fill_colour[3])  # a
                    pixels_changed += 1
                elif (r, g, b, a) == self.piece_outline_colour:
                    # Change the piece outline colour
                    # to what the user selected
                    newstr += chr(outline_colour[0])  # r
                    newstr += chr(outline_colour[1])  # g
                    newstr += chr(outline_colour[2])  # b
                    newstr += chr(outline_colour[3])  # a
                    pixels_changed += 1
                elif (r, g, b, a) == self.piece_kanji_colour:
                    # Change the piece kanji colour
                    # to what the user selected
                    newstr += chr(kanji_colour[0])  # r
                    newstr += chr(kanji_colour[1])  # g
                    newstr += chr(kanji_colour[2])  # b
                    newstr += chr(kanji_colour[3])  # a
                    pixels_changed += 1
                else:
                    # other colour - no change                   
                    newstr += chr(r)
                    newstr += chr(g)
                    newstr += chr(b)
                    newstr += chr(a)

            if pixels_changed == 0:
                print "Unable to change piece colour in pieces.py - maybe piece images have been corrupted"

            pixbuf[i] = gtk.gdk.pixbuf_new_from_data(newstr, pb.get_colorspace(), pb.get_has_alpha(), pb.get_bits_per_sample(), pb.get_width(), pb.get_height(), pb.get_rowstride())
        return pixbuf


    def getpixbuf(self, piece):
        # pieces contains the list of possible pieces
        pieces = [" -", " p", " l", " n", " s", " g", " b", " r", " k", "+p", "+l", "+n", "+s", "+b", "+r", " P", " L", " N", " S", " G", " B", " R", " K", "+P", "+L", "+N", "+S", "+B", "+R"]         

        try:
            idx = pieces.index(piece) 
        except ValueError, ve:
            traceback.print_exc()
            print "error piece not found, piece =", piece 

        if self.pieceset == 'eastern':
            pixbuf = self.piece_pixbuf[idx]
        elif self.pieceset == 'western':
            pixbuf = self.western_piece_pixbuf[idx]
        elif self.pieceset == 'custom':
            pixbuf = self.custom_piece_pixbuf[idx]
        else:
            print "invalid pieceset in getpixbuf in pieces.py:",self.pieceset
            pixbuf = self.piece_pixbuf[idx]   # eastern        

        width = int(self.scale_factor * 64)
        height = int(self.scale_factor * 64)
        spb = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_HYPER)        
        return spb                


    def get_pieceset(self):
        return self.pieceset


    def set_pieceset(self, pieceset):
        self.pieceset = pieceset


    def get_custom_pieceset_path(self):
        return self.custom_piece_path


    def set_custom_pieceset_path(self, path):
        self.custom_piece_path = path


    def set_scale_factor(self, factor):        
        if factor < 0:                      
            return     
        elif factor < 0.3:
            factor = 0.3            
        elif factor > 3.0:
            factor = 3.0 
        
        self.scale_factor = factor * 0.95            
        


