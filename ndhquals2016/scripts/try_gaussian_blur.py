from PIL import Image, ImageFont, ImageChops, ImageDraw, ImageFilter
import cv2 
import numpy as np

# Radius value + MAX radius values to test
RADIUS = 0
RADIUS_MAX = 100

# Max first columns to compare
INIT_NB_COLUMNS = 3

# When creating an image, we use this size and this text position
WIDTH = 800
HEIGHT = 50
TEXT_POS = (200,12)

FOREGROUND = (255, 255, 255)
BG_COLOR = "#000000"
BACKGROUND = (0, 0, 0)

TEXT_SIZE = 24
#FONT_PATH = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
FONT_PATH = './FreeSans.ttf'
FONT = ImageFont.truetype(FONT_PATH, TEXT_SIZE)

ALPHABET = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz[]'

# Retrieving the chall file and extracting the flag within
FLAG_PATH = 'moleman.png'
FLAG_BOX = (500, 150, 650, 400)

# TAG used to retrieve the RADIUS and the position of the flag.
TAG = 'H'

def create_image(text, radius):
    '''
    Function used to create an image :
        - text = the text to add to this image
        - radius = radius to use with the gaussian blur
    '''
    im = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    draw.text(TEXT_POS, text, font=FONT, fill=FOREGROUND)

    del draw

    im = im.filter(ImageFilter.GaussianBlur(radius=radius))
    #im.show()

    return im

def init_find_first_column(img):
    '''
    Function used to find the first column with not null values.
    We will use it to start the init phase (find the radius and the text position).
    '''
    width, height = img.size
    pixels = img.load()

    for i in range(width):
        for j in range(height):
            if pixels[i,j] != BACKGROUND:
                return i

    return None

def init_find_init_box(img):
    '''
    Function used to find the first INIT_NB_COLUMNS to compare between our created image and the blurred flag during the init phase (find the radius and the text position).
    '''
    width, height = img.size
    pixels = img.load()
    
    # Find the first column not null
    first_column = init_find_first_column(img)
    first_line = None
    last_line = None

    # Find the first and the last lines to complete the box (we will use only the INIT_NB_COLUMNS)
    for j in range(height):
        for i in range(first_column, first_column + INIT_NB_COLUMNS):
            if pixels[i,j] != BACKGROUND:
                last_line = j
                if first_line == None:
                    first_line = j

    return (first_column, first_line, first_column + INIT_NB_COLUMNS, last_line)

def test_radius(flag, template):
    '''
    Function to test a radius
        - flag = flag file
        - template = our template to test

    For more informations see : http://docs.opencv.org/3.1.0/d4/dc6/tutorial_py_template_matching.html
    '''
    #flag.show()
    #template.show()

    # Converting a PIL image to a cv2 image
    flag2 = cv2.cvtColor(np.array(flag), cv2.COLOR_RGB2BGR)
    template2 = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)

    c,w,h = template2.shape[::-1]

    # All the 6 methods for comparison in a list
    # I wanted to be sure to find our template
    methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR','cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
    #methods = ['cv2.TM_CCOEFF_NORMED']

    # Using comparison methods (matchTemplate) to find our template in the flag image
    for meth in methods:
        flag_temp = flag2.copy()
        method = eval(meth)

        # Apply template Matching
        res = cv2.matchTemplate(flag_temp,template2,method)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc

        box = (top_left[0], top_left[1], top_left[0]+w, top_left[1]+h)
        temp = flag.crop(box)

        '''
        temp.show()
        template.show()
        ImageChops.difference(temp, template).show()
        '''

        pixels0 = temp.load()
        pixels1 = template.load()

        # The matchTemplate function do not test an exact image, it can be more or less the same.
        # So we have to test if the template is really where matchTemplate say.
        is_equal = True
        for i in range(w):
            for j in range(h):
                if pixels0[i,j] != pixels1[i,j] :
                    is_equal = False
                    break

        '''
        print is_equal
        print "#################"
        '''

        # If it's equal, we return the position of our match
        if is_equal:
            return top_left

    return None

def init_bf(flag):
    '''
    Function to BF the radius.
    If we find the radius, we also know the text potition of our flag.
    '''
    for i in range(RADIUS_MAX):
        template = create_image(TAG, i)
        #template.show()

        box = init_find_init_box(template)
        #print "box = (%d, %d, %d, %d)" % (box[0],box[1],box[2],box[3])
        #box = (first_column, 0, first_column + INIT_NB_COLUMNS, HEIGHT)

        template = template.crop(box)
        #template.show()

        top_left = test_radius(flag, template)
        #print "top_left = (%d, %d)" % (top_left[0], top_left[1])

        if top_left != None :
            text_pos = (TEXT_POS[0] + top_left[0] - box[0], TEXT_POS[1] + top_left[1] - box[1])
            return (i, text_pos)
        
    return None

def count_same_columns(img0, img1):
    '''
    Function to count the number of equal columns between 2 images (img0 and img1).
    '''
    width, height = img0.size
    pixels0 = img0.load()
    pixels1 = img1.load()

    nb_same_columns = 0

    for i in range(width):
        for j in range(height):
            if pixels0[i,j] != pixels1[i,j]:
               return nb_same_columns
        nb_same_columns += 1    

    return nb_same_columns

def bf_char(im0, prefix):
    '''
    Function used to BF caracter by caracter the flag.
    At this point we know the radius and the text position of the flag.
        - im0 = the flag image
        - prefix = the string already found
    '''
    best_score = 0
    best_char = ''

    # We are trying to find the best charater (the one with the most equals columns)
    for c in ALPHABET:
        im1 = create_image('%s%s' % (prefix, c), RADIUS)

        '''
        im1.save('tests/%s_%s.jpg' % (prefix, c))
        ImageChops.difference(im0, im1).save('tests/diff_%s.jpg' % c)
        '''

        same_columns = count_same_columns(im0, im1)
        #print "CHAR = %s : SAME COLUMNS : %d" % (c, same_columns)

        if same_columns > best_score :
            best_score = same_columns
            best_char = c

    print best_char

    return best_char

def bf(flag):
    '''
    Main BF function.
    '''
    string = TAG

    i = 0
    while string[-1:] != ']':
        string += bf_char(flag, string)[0][0]
        i += 1

    print "FLAG = %s" % string

if __name__ == '__main__':
    # Crop the flag area :
    print "[i] Retrieving a char from the second line"
    flag = Image.open(FLAG_PATH)
    flag = flag.crop(FLAG_BOX)
    flag.show()

    # Find the RADIUS and the TEXT_POS
    print "[i] Finding the radius and the text position"
    (RADIUS,TEXT_POS) = init_bf(flag) 
    print "RADIUS = %d, TEXT_POS = (%d,%d)" % (RADIUS, TEXT_POS[0], TEXT_POS[1])

