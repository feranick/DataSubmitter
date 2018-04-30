import base64

'''
img = Image.open('1.png')
img = Binary(img)

imgByteArr = io.BytesIO()
img.save(imgByteArr, format='PNG')
imgByteArr = imgByteArr.getvalue()

'''
with open("1.png", "rb") as imageFile:
    str = base64.b64encode(imageFile.read())
    #store str in mongo

print(str)
print(base64.b64decode(str))

with open("test2.txt", "wb") as fs:
    fs.write(str)

with open("test2.jpg", "wb") as fh:
    fh.write(base64.b64decode(str))
