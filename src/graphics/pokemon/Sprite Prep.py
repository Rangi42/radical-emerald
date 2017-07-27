# Run this if any sprites in /Sheets are changed to convert them to binary.
# If you can't get it to work bug Doesnt to run it for you.

from PIL import Image
import os

def subfinder(mylist, pattern):

    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            return i
    return -1

def LZ77Compress(data) :
   compressed = [0x10]
   data_length = len(data)
   compressed.append(data_length % 256)
   compressed.append((data_length >> 8) % 256)
   compressed.append((data_length >> 16) % 256)

   index = 0
   w = 4095
   window = None
   lookahead = None
   while True :
      bits = []
      check = None
      currCompSet = []
      for n in range(8) :
         if index < w : window = data[:index]
         else: window = data[index-w:index]
         lookahead = data[index:]
         if lookahead == [] :
            if bits != [] :
               while len(bits) != 8 :
                  bits.append(0)
                  currCompSet.append(0)
               bitfield = bits[7] + 2*bits[6] + 4*bits[5] + 8*bits[4] \
                          + 16*bits[3] + 32*bits[2] + 64*bits[1] + 128*bits[0]
               compressed.append(bitfield)
               compressed += currCompSet
            break
         check = subfinder(window, lookahead[0:3]) # Need to find at least a 3 byte match
         if check == -1 :
            index += 1
            bits.append(0)
            currCompSet += [lookahead[0]]
         else :
            bits.append(1) # Compressed data
            length = 2
            while check != -1 and length < 18 :
               store_length = length
               length += 1
               store_check = check
               check = subfinder(window, lookahead[0:length])
            index += store_length
            store_length -= 3
            position = len(window)-store_check-1
            store_length = store_length << 12
            pos_and_len = store_length | position
            currCompSet.append(pos_and_len >> 8)
            currCompSet.append(pos_and_len % 256)
      if lookahead == [] :
         if bits != [] :
            while len(bits) != 8 :
               bits.append(0)
               currCompSet.append(0)
            bitfield = bits[7] + 2*bits[6] + 4*bits[5] + 8*bits[4] \
                     + 16*bits[3] + 32*bits[2] + 64*bits[1] + 128*bits[0]
            compressed.append(bitfield)
            compressed += currCompSet
         break
      bitfield = bits[7] + 2*bits[6] + 4*bits[5] + 8*bits[4] \
               + 16*bits[3] + 32*bits[2] + 64*bits[1] + 128*bits[0]
      compressed.append(bitfield)
      compressed += currCompSet
   return compressed
         

def ConvertImageToGBA(image, size=(64,64)) :
   data = list(image.getdata())
   palette = image.getpalette()
   height = size[1]
   width = size[0]
   blocks = []
   block_num = int(width/8)
   for w in range(int(height/8)) :
      for x in range(8) :
         block_num -= int(width/8)
         for y in range(int(width/8)) :
            for z in range(8) :
               value = data[0]
               try: blocks[block_num]
               except: blocks.append([])
               blocks[block_num].append(value)
               data = data[1:]
            block_num += 1
      block_num += int(width/8)

   bgslot = blocks[0][0]
   for i in range(len(blocks)) :
      for j in range(len(blocks[i])) :
         if blocks[i][j] == bgslot :
            blocks[i][j] = 0
         elif blocks[i][j] == 0 :
            blocks[i][j] = bgslot
   tmp = palette[0]
   tmp2 = palette[1]
   tmp3 = palette[2]
   palette[0] = palette[3*bgslot]
   palette[1] = palette[3*bgslot + 1]
   palette[2] = palette[3*bgslot + 2]
   palette[bgslot*3] = tmp
   palette[bgslot*3 + 1] = tmp2
   palette[bgslot*3 + 2] = tmp3
   gbapal = []
   for i in range(16) :
      r = palette[0] >> 3
      g = palette[1] >> 3
      b = palette[2] >> 3
      gbacolor = r + (g << 5) + (b << 10)
      palette = palette[3:]
      gbapal.append(gbacolor % 256)
      gbapal.append(gbacolor >> 8)
   values = []
   for b in blocks :
      values += b
   i = 0
   gbaimg = []
   while i < len(values) :
      gbaimg.append((values[i+1] << 4) + values[i])
      i += 2
   return (gbaimg, gbapal)

def LoadSheetSprite(name):
   filename = "Sheets/" + name + ".png"
   raw = Image.open(filename)
   front = None
   shiny = None
   secondframe = False
   if raw.size == (256,64) :
       front = raw.copy().crop((0, 0, 64, 64))
       shiny = raw.copy().crop((64, 0, 128, 64))
   elif raw.size == (256,128) :
       front = raw.copy().crop((0, 0, 64, 128))
       shiny = raw.copy().crop((64, 0, 128, 128))
   else:
      print(name + "is fucked")
      return

   back = raw.copy().crop((128, 0, 192, 64))
   shinyback = raw.copy().crop((192, 0, 256, 64))
   frontback = Image.new("RGB", (64,128))
   frontback.paste(front, (0,0))
   frontback.paste(back, (0,64))
   shinyfb = Image.new("RGB", (64, 128))
   shinyfb.paste(shiny, (0,0))
   shinyfb.paste(shinyback, (0,64))
   if frontback.mode != "P":
       frontback = frontback.convert("RGB")
       frontback = frontback.convert("P", palette=Image.ADAPTIVE, colors=16)
   else:
       if len(frontback.getcolors()) > 16:
           tmp = frontback.convert("RGB")
           frontback = tmp.convert("P", palette=Image.ADAPTIVE, colors=16)
   if shinyfb.mode != "P":
       shinyfb = shinyfb.convert("RGB")
       shinyfb = shinyfb.convert("P", palette=Image.ADAPTIVE, colors=16)
   else:
       if len(shinyfb.getcolors()) > 16:
           tmp = shinyfb.convert("RGB")
           shinyfb = tmp.convert("P", palette=Image.ADAPTIVE, colors=16)

   fbimg, npal = ConvertImageToGBA(frontback, (64, 128))
   fimg = fbimg[0:2048]
   bimg = fbimg[2048:]
   simg, spal = ConvertImageToGBA(shinyfb)

   # Resolve the shiny palette. This is kind of a pain...
   fbdata = list(frontback.getdata())
   shdata = list(shinyfb.getdata())
   shinypal = shinyfb.getpalette()
   newshinypal = shinypal.copy()
   for i in range(len(fbdata)) :
      normalval = fbdata[i]
      shinyval = shdata[i]
      if normalval != shinyval :
         newshinypal[normalval*3  ] = shinypal[shinyval*3]
         newshinypal[normalval*3+1] = shinypal[shinyval*3+1]
         newshinypal[normalval*3+2] = shinypal[shinyval*3+2]

   # Convert shiny palette to GBA format
   gbashinypal = []
   for i in range(16) :
      r = newshinypal[0] >> 3
      g = newshinypal[1] >> 3
      b = newshinypal[2] >> 3
      gbacolor = r + (g << 5) + (b << 10)
      newshinypal = newshinypal[3:]
      gbashinypal.append(gbacolor % 256)
      gbashinypal.append(gbacolor >> 8)

   # Ensure the background color is in slot 0
   bgindex = fbdata[0]
   tmp  = gbashinypal[bgindex*2]
   tmp2 = gbashinypal[bgindex*2 + 1]
   gbashinypal[bgindex*2] = gbashinypal[0]
   gbashinypal[bgindex*2+1] = gbashinypal[1]
   gbashinypal[0] = tmp
   gbashinypal[1] = tmp2
      
   
   with open("Raw\\" + name + "F.bin", "w+b") as file:
      file.write(bytes(LZ77Compress(fimg)))
   with open("Raw\\" + name + "B.bin", "w+b") as file:
      file.write(bytes(LZ77Compress(bimg)))
   with open("Raw\\" + name + "Pal.bin", "w+b") as file:
      file.write(bytes(LZ77Compress(npal)))
   with open("Raw\\" + name + "SPal.bin", "w+b") as file:
      file.write(bytes(LZ77Compress(gbashinypal)))


names = []

with open("Graphics.s", "w") as out :
    for root, dirs, files in os.walk("Sheets/") :
        for file in files :
            name = file.replace(".png", "")
            out.write("poke" + name + "FSprite:\n.incbin \"graphics/pokemon/raw/" + name + "F.bin\"\n.align 2\n" )
            out.write("poke" + name + "BSprite:\n.incbin \"graphics/pokemon/raw/" + name + "B.bin\"\n.align 2\n" )
            out.write("poke" + name + "Pal:\n.incbin \"graphics/pokemon/raw/" + name + "Pal.bin\"\n.align 2\n" )
            out.write("poke" + name + "SPal:\n.incbin \"graphics/pokemon/raw/" + name + "SPal.bin\"\n.align 2\n" )
            names.append(name)
            LoadSheetSprite(file.replace(".png", ""))

    out.write("MonFrontSpriteTable:\n")
    i = 0
    for n in names :
        out.write(".4byte poke" + n + "FSprite\n.2byte 0x800\n.2byte " + str(i) + "\n")
        i += 1

    out.write("MonBackSpriteTable:\n")
    i = 0
    for n in names :
        out.write(".4byte poke" + n + "BSprite\n.2byte 0x800\n.2byte " + str(i) + "\n")
        i += 1

    out.write("MonPaletteTable:\n")
    i = 0
    for n in names :
        out.write(".4byte poke" + n + "Pal\n.2byte " + str(i) + "\n.2byte 0\n")
        i += 1

    out.write("MonSPaletteTable:\n")
    i = 0
    for n in names :
        out.write(".4byte poke" + n + "SPal\n.2byte " + str(i + 999) + "\n.2byte 0\n")
        i += 1
