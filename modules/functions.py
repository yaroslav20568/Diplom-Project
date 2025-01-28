from PIL import Image
import cv2
import pytesseract
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from itertools import groupby
import uuid
import re

# ------------ФУНКЦИИ------------

# функция нахождения постоянного значения x оY и y oX и удаление чёрной вертикальной линии
def findAxisConstValue(array, coordParam, black_pixels, im, col_white):
    black_pixels_X_with_count = [{coordParam: i, 'count': array.count((i))} for i in array]
    black_pixels_X_with_count_sort_by_count = sorted(black_pixels_X_with_count, key=lambda x: x['count'], reverse=True)
    withoutDuplicates = [el for el, _ in groupby(black_pixels_X_with_count_sort_by_count)]
    axisConstValue = withoutDuplicates[0][coordParam]

    if coordParam == 'x' and withoutDuplicates[0]['count'] - withoutDuplicates[1]['count'] <= 100:
        vertLineX = withoutDuplicates[1]['x']

        vertLineCoords = []
        for pixel in black_pixels:
            if vertLineX == pixel['x']:
                vertLineCoords.append({'x': pixel['x'], 'y': pixel['y']})
        print('vertLineCoords: ', vertLineCoords)

        for x in range(im.size[0]):
            for y in range(im.size[1]):
                if x == vertLineX and (
                        y >= vertLineCoords[0]['y'] or y <= vertLineCoords[len(vertLineCoords) - 1]['y']):
                    im.putpixel((x, y), col_white)

    return axisConstValue

# функция удаления лишних пикселей в столбце и строке в котором есть координаты оY и oX
def removeUnnecessaryPixels(array, coordParam):
    tempArray = []
    for i in range(len(array)):
        if array[i][coordParam] == array[i - 1][coordParam] + 1 or i == 0:
            tempArray.append({'x': array[i]['x'], 'y': array[i]['y']})
        else:
            break
    return tempArray

# функция нахождения порога у мал и бол штрихов на оX и oY
def thresholdStroke(axis, im, axis_x_const_y, axisXCoords, col_black, axis_y_const_x, axisYCoords):
    threshols = []
    if axis == 'x':
        for x in range(im.size[0]):
            k = 0
            for y in range(im.size[1]):
                if y >= axis_x_const_y and x >= axisXCoords[0]['x'] and x <= axisXCoords[len(axisXCoords) - 1]['x'] and \
                        im.getpixel((x, axis_x_const_y + k + 1)) == col_black:
                    k = k + 1
                if y == im.size[1] - 1 and k != 0:
                    threshols.append(k)
        threshols = list(set(threshols))
        return {'smallThresholsX': threshols[0], 'bigThresholsX': threshols[1]}
    else:
        for y in range(im.size[1]):
            k = 0
            for x in reversed(range(im.size[0])):
                if x <= axis_y_const_x and y >= axisYCoords[0]['y'] and y <= axisYCoords[len(axisYCoords) - 1]['y'] and \
                        im.getpixel((axis_y_const_x - k - 1, y)) == col_black:
                    k = k + 1
                if x == 0 and k != 0:
                    threshols.append(k)
        threshols = list(set(threshols))
        return {'smallThresholsY': threshols[0], 'bigThresholsY': threshols[1]}

# функция нахождение штрихов по порогу на оX и oY
def findStrokes(array, axis, threshold, im, col_black):
    strokeArray = []

    if axis == 'x':
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                if im.getpixel((x, y)) == col_black:
                    elem = list(filter(lambda el: el['x'] == x and el['y'] == y, array))
                    if len(elem) != 0 and im.getpixel((x, y + threshold)) == col_black:
                        strokeArray.append({'x': x, 'y': y})
        return [strokeArray[0], strokeArray[len(strokeArray) - 2], strokeArray[len(strokeArray) - 1]]
    else:
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                if im.getpixel((x, y)) == col_black:
                    elem = list(filter(lambda el: el['x'] == x and el['y'] == y, array))
                    if len(elem) != 0 and im.getpixel((x - threshold, y)) == col_black:
                        strokeArray.append({'x': x, 'y': y})
        return [strokeArray[len(strokeArray) - 1], strokeArray[1], strokeArray[0]]

# функция распознания значений интенсивности и волнового числа с картинки
def recognizeValue(img):
    im_tesseract = cv2.resize(img, None, fx=9, fy=9)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    config = r'--oem 3 --psm 6 outputbase digits'
    string = pytesseract.image_to_string(im_tesseract, config=config)
    value = int(string.split()[0]) if len(string) > 4 else int(string)
    return value

# функция нахождения пикселей для каждой точки образца
def findPixelsForPoint(color, cropIm):
    pixelsArray = []
    arrayX = []
    arrayY = []
    for x in range(cropIm.size[0]):
        k = 0
        for y in range(cropIm.size[1]):
            if k == 1:
                k == 0
                break
            if cropIm.getpixel((x, y)) == color:
                k = k + 1
                pixelsArray.append({'x': x, 'y': y})
                arrayX.append(x)
                arrayY.append(y)

    listX = list(range(pixelsArray[0]['x'], pixelsArray[len(pixelsArray) - 1]['x'] + 1))
    interpArrayY = np.interp(listX, arrayX, arrayY)

    newArray = []
    for i, y in enumerate(interpArrayY):
        newArray.append({'x': listX[i], 'y': y})

    return newArray

# функция получения и визуализации пиков
def getPeaks(pointArray, img_1px_equel_func_valueX, firstBigStrokeY, beginning_of_coord, cropIm, 
             img_1px_equel_func_valueY, minValueY, imgPath, pointNumberImg):
    arrayX = []
    arrayY = []
    for pixel in pointArray:
        arrayX.append(pixel['x'])
        arrayY.append(pixel['y'])

    intensityArray = []
    waveNumberArray = []
    for i, x in enumerate(arrayX):
        waveNumberArray.append(x * img_1px_equel_func_valueX)
    for i, y in enumerate(arrayY):
        if firstBigStrokeY['y'] == beginning_of_coord['y']:
            intensityArray.append((cropIm.size[1] - y) * img_1px_equel_func_valueY + minValueY)
        else:
            diffStrokeY = beginning_of_coord['y'] - firstBigStrokeY['y']

            if y < firstBigStrokeY['y']:
                intensityArray.append((firstBigStrokeY['y'] - y) * img_1px_equel_func_valueY + minValueY)
            else:
                intensityArray.append(((cropIm.size[1] - y) * ((minValueY - 0) / diffStrokeY)))

    intensityArray = np.array(intensityArray)
    waveNumberArray = np.array(waveNumberArray)

    peaks = find_peaks(intensityArray, height=1, threshold=1, distance=1)
    height = peaks[1]['peak_heights']
    peak_pos = waveNumberArray[peaks[0]]

    plt.plot(waveNumberArray, intensityArray)
    plt.scatter(peak_pos, height, color='r', s=15, marker='D', label='Peak')
    plt.legend()
    plt.grid()
    plt.xlabel('Wave number', fontsize=12)
    plt.ylabel('Intensity', fontsize=12)
    newStr = imgPath.replace("samples", "visualization_graphs").replace("bmp", "jpg").replace(".", f'({pointNumberImg}).')
    plt.savefig(f'{newStr}')
    plt.clf()

    peaksArray = []
    for i in peaks[0]:
        peaksArray.append({'waveNumber': waveNumberArray[i], 'intensity': intensityArray[i]})
	
    pointNumberImg = pointNumberImg + 1

    return peaksArray, pointNumberImg

# функция нахождения уникальных пиков
def setUniqPeaks(currPeaksArray, peaksArrays):
    for peaksArray in peaksArrays:
        for currPeak in currPeaksArray:
            for peak in peaksArray:
                if currPeak['waveNumber'] == peak['waveNumber']:
                    currPeak['noUniq'] = True
                    peak['noUniq'] = True

    return currPeaksArray

# функция записи в Microsoft Excel значений пиков
def writeToDB(array, pointNumber, myCursor, myDb):
    myCursor.execute(f"INSERT INTO characteristics(textInfo) VALUES('Точка № {pointNumber}');")
    myDb.commit()

    for i in range(len(array)):
        myCursor.execute(f"INSERT INTO characteristics(waveNumber, intensity, uniq) VALUES({array[i]['waveNumber']}, {array[i]['intensity']}, {False if 'noUniq' in array[i] else True})")
        myDb.commit()

    pointNumber = pointNumber + 1
    return pointNumber

def writeToWaveNumberArray(waveNumberArray, pointArrayPeaks):
    for peak in pointArrayPeaks:
        waveNumberArray.append(peak['waveNumber'])

# ------------ФУНКЦИИ------------

# функция обработки изображения и получения данных
def getResultsFromImg(imgPath, sampleNumber, waveNumberArray, myCursor, myDb):
    im = Image.open(imgPath)
    im = im.convert('RGB')

    col_black = (0, 0, 0)
    col_white = (255, 255, 255)

    # массивы чёрных пикселей x, y, xy
    black_pixels_X = []
    black_pixels_Y = []
    black_pixels = []
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if im.getpixel((x, y)) == col_black:
                black_pixels_X.append(x)
                black_pixels_Y.append(y)
                black_pixels.append({'x': x, 'y': y})

    # нахождения постоянного значения x оY и y oX и удаление чёрной вертикальной линии
    axis_y_const_x = findAxisConstValue(black_pixels_X, 'x', black_pixels, im, col_white)
    axis_x_const_y = findAxisConstValue(black_pixels_Y, 'y', black_pixels, im, col_white)

    # нахождение всех чёрных пикселей в столбце в котором находится ось Y
    axisYCoords = []
    for pixel in black_pixels:
        if axis_y_const_x == pixel['x']:
            axisYCoords.append({'x': pixel['x'], 'y': pixel['y']})

    # нахождение всех чёрных пикселей в столбце в котором находится ось X
    axisXCoords = []
    for pixel in black_pixels:
        if axis_x_const_y == pixel['y']:
            axisXCoords.append({'x': pixel['x'], 'y': pixel['y']})

    # удаления лишних пикселей в столбце и строке в котором есть координаты оY и oX
    axisYCoords = removeUnnecessaryPixels(axisYCoords, 'y')
    axisXCoords = removeUnnecessaryPixels(axisXCoords, 'x')

    print('axisYCoords: ', axisYCoords)
    print('axisXCoords: ', axisXCoords)

    # находим начало координат(пересечение oY и oX)
    beginning_of_coord = 0
    for axisYCoord in axisYCoords:
        for axisXcoord in axisXCoords:
            if axisYCoord['x'] == axisXcoord['x'] and axisYCoord['y'] == axisXcoord['y']:
                beginning_of_coord = axisXcoord
                break

    print('beginning_of_coord: ', beginning_of_coord)

    # нахождение порога у мал и бол штрихов на оX и oY
    thresholdsX = thresholdStroke('x', im, axis_x_const_y, axisXCoords, col_black, axis_y_const_x, axisYCoords)
    thresholdsY = thresholdStroke('y', im, axis_x_const_y, axisXCoords, col_black, axis_y_const_x, axisYCoords)

    print('thresholdX: ', thresholdsX)
    print('thresholdY: ', thresholdsY)

    # нахождение штрихов по порогу на оX и oY
    firstBigStrokeX, secondLastBigStrokeX, lastBigStrokeX = findStrokes(axisXCoords, 'x', thresholdsX['bigThresholsX'], 
                                                        im, col_black)
    firstBigStrokeY, secondLastBigStrokeY, lastBigStrokeY = findStrokes(axisYCoords, 'y', thresholdsY['bigThresholsY'], 
                                                        im, col_black)
    _, secondSmallStrokeX, _ = findStrokes(axisXCoords, 'x', thresholdsX['smallThresholsX'], im, col_black)

    print('firstBigStrokeX: ', firstBigStrokeX, 'lastBigStrokeX: ', lastBigStrokeX)
    print('firstBigStrokeY: ', firstBigStrokeY, 'lastBigStrokeY: ', lastBigStrokeY)
    print('secondSmallStrokeX: ', secondSmallStrokeX)

    # распознование максимального значения интенсивности на oY и волнового числа на oX с картинки
    diffBigStrokeY = int(abs((lastBigStrokeY['y'] - secondLastBigStrokeY['y']) / 2))
    im_cropMaxY = im.crop(
        (lastBigStrokeY['x'] - thresholdsX['bigThresholsX'] - 40, lastBigStrokeY['y'] - diffBigStrokeY,
         lastBigStrokeY['x'] - thresholdsY['bigThresholsY'], lastBigStrokeY['y'] + diffBigStrokeY))
    im_cropMaxY.save('img/crops/cropMaxY.png')

    diffBigStrokeX = int(abs((lastBigStrokeX['x'] - secondLastBigStrokeX['x']) / 2))
    im_cropMaxX = im.crop((lastBigStrokeX['x'] - diffBigStrokeX, lastBigStrokeX['y'] + thresholdsX['bigThresholsX'] + 1,
                           lastBigStrokeX['x'] + diffBigStrokeX, lastBigStrokeX['y'] + 25))
    im_cropMaxX.save('img/crops/cropMaxX.png')

    maxValueY = recognizeValue(cv2.imread("img/crops/cropMaxY.png", cv2.IMREAD_GRAYSCALE))
    maxValueX = recognizeValue(cv2.imread("img/crops/cropMaxX.png", cv2.IMREAD_GRAYSCALE))

    print('maxValueY: ', maxValueY)
    print('maxValueX: ', maxValueX)

    # распознование минимального значения интенсивности на oY и волного числа oX с картинки
    im_cropMinY = im.crop(
        (firstBigStrokeY['x'] - thresholdsY['bigThresholsY'] - 40, firstBigStrokeY['y'] - diffBigStrokeY,
         firstBigStrokeY['x'] - thresholdsY['bigThresholsY'], firstBigStrokeY['y'] + diffBigStrokeY))
    im_cropMinY.save('img/crops/cropMinY.png')

    im_cropMinX = im.crop(
        (firstBigStrokeX['x'] - diffBigStrokeX, firstBigStrokeX['y'] + thresholdsX['bigThresholsX'] + 1,
         firstBigStrokeX['x'] + diffBigStrokeX, firstBigStrokeX['y'] + 25))
    im_cropMinX.save('img/crops/cropMinX.png')

    minValueY = recognizeValue(cv2.imread("img/crops/cropMinY.png", cv2.IMREAD_GRAYSCALE))
    minValueX = recognizeValue(cv2.imread("img/crops/cropMinX.png", cv2.IMREAD_GRAYSCALE))

    print('minValueY: ', minValueY)
    print('minValueX: ', minValueX)

    # сколько 1px занимает значений интенсивности и волнового числа
    img_1px_equel_func_valueX = (maxValueX - minValueX) / (lastBigStrokeX['x'] - beginning_of_coord['x'])
    img_1px_equel_func_valueY = (maxValueY - minValueY) / (firstBigStrokeY['y'] - lastBigStrokeY['y'])

    print('img_1px_equel_func_valueX: ', img_1px_equel_func_valueX)
    print('img_1px_equel_func_valueY: ', img_1px_equel_func_valueY)

    # вырезаем графики
    cropIm = im.crop((lastBigStrokeY['x'] + 1, 0, secondSmallStrokeX['x'], secondSmallStrokeX['y']))
    cropIm.save("img/crops/cropIm.bmp")

    # нахождение пикселей для каждой точки образца
    firstPointArray = findPixelsForPoint((0, 0, 0), cropIm)
    secondPointArray = findPixelsForPoint((255, 0, 0), cropIm)
    thirdPointArray = findPixelsForPoint((0, 0, 255), cropIm)
    fourthPointArray = findPixelsForPoint((0, 128, 128), cropIm)
    fifthPointArray = findPixelsForPoint((255, 0, 255), cropIm)

    print('firstPointArray: ', firstPointArray)
    print('secondPointArray: ', secondPointArray)
    print('thirdPointArray: ', thirdPointArray)
    print('fourthPointArray: ', fourthPointArray)
    print('fifthPointArray: ', fifthPointArray)

    # получаем и визуализируем пики
    pointNumberImg = 1
	
    firstPointArrayPeaks, pointNumberImg = getPeaks(firstPointArray, img_1px_equel_func_valueX, firstBigStrokeY, 
                                    beginning_of_coord, cropIm, img_1px_equel_func_valueY, minValueY, imgPath, pointNumberImg)
    secondPointArrayPeaks, pointNumberImg = getPeaks(secondPointArray, img_1px_equel_func_valueX, firstBigStrokeY, 
                                     beginning_of_coord, cropIm, img_1px_equel_func_valueY, minValueY, imgPath, pointNumberImg)
    thirdPointArrayPeaks, pointNumberImg = getPeaks(thirdPointArray, img_1px_equel_func_valueX, firstBigStrokeY, 
                                    beginning_of_coord, cropIm, img_1px_equel_func_valueY, minValueY, imgPath, pointNumberImg)
    fourthPointArrayPeaks, pointNumberImg = getPeaks(fourthPointArray, img_1px_equel_func_valueX, firstBigStrokeY, 
                                     beginning_of_coord, cropIm, img_1px_equel_func_valueY, minValueY, imgPath, pointNumberImg)
    fifthPointArrayPeaks, pointNumberImg = getPeaks(fifthPointArray, img_1px_equel_func_valueX, firstBigStrokeY, 
                                    beginning_of_coord, cropIm, img_1px_equel_func_valueY, minValueY, imgPath, pointNumberImg)

    print('firstPointArrayPeaks: ', firstPointArrayPeaks)
    print('secondPointArrayPeaks: ', secondPointArrayPeaks)
    print('thirdPointArrayPeaks: ', thirdPointArrayPeaks)
    print('fourthPointArrayPeaks: ', fourthPointArrayPeaks)
    print('fifthPointArrayPeaks: ', fifthPointArrayPeaks)

    # нахождение уникальных пиков
    firstPointArrayPeaks = setUniqPeaks(firstPointArrayPeaks,
                                       [secondPointArrayPeaks, thirdPointArrayPeaks, fourthPointArrayPeaks,
                                        fifthPointArrayPeaks])
    secondPointArrayPeaks = setUniqPeaks(secondPointArrayPeaks,
                                        [firstPointArrayPeaks, thirdPointArrayPeaks, fourthPointArrayPeaks,
                                         fifthPointArrayPeaks])
    thirdPointArrayPeaks = setUniqPeaks(thirdPointArrayPeaks,
                                       [firstPointArrayPeaks, secondPointArrayPeaks, fourthPointArrayPeaks,
                                        fifthPointArrayPeaks])
    fourthPointArrayPeaks = setUniqPeaks(fourthPointArrayPeaks,
                                        [firstPointArrayPeaks, secondPointArrayPeaks, thirdPointArrayPeaks,
                                         fifthPointArrayPeaks])
    fifthPointArrayPeaks = setUniqPeaks(fifthPointArrayPeaks,
                                       [firstPointArrayPeaks, secondPointArrayPeaks, thirdPointArrayPeaks,
                                        fourthPointArrayPeaks])

    print('firstPointArrayPeaks: ', firstPointArrayPeaks)
    print('secondPointArrayPeaks: ', secondPointArrayPeaks)
    print('thirdPointArrayPeaks: ', thirdPointArrayPeaks)
    print('fourthPointArrayPeaks: ', fourthPointArrayPeaks)
    print('fifthPointArrayPeaks: ', fifthPointArrayPeaks)


    writeToWaveNumberArray(waveNumberArray, firstPointArrayPeaks)
    writeToWaveNumberArray(waveNumberArray, secondPointArrayPeaks)
    writeToWaveNumberArray(waveNumberArray, thirdPointArrayPeaks)
    writeToWaveNumberArray(waveNumberArray, fourthPointArrayPeaks)
    writeToWaveNumberArray(waveNumberArray, fifthPointArrayPeaks)
    # for peak in secondPointArrayPeaks:
    #     waveNumberArray.append(peak['waveNumber'])
        
    # for peak in thirdPointArrayPeaks:
    #     waveNumberArray.append(peak['waveNumber'])
        
    # for peak in fourthPointArrayPeaks:
    #     waveNumberArray.append(peak['waveNumber'])
        
    # for peak in fifthPointArrayPeaks:
    #     waveNumberArray.append(peak['waveNumber'])


    pointNumber = 1

    myCursor.execute(f"INSERT INTO characteristics(textInfo) VALUES('Образец № {sampleNumber}');")
    myDb.commit()

    # запись значений пиков в Microsoft Excel
    pointNumber = writeToDB(firstPointArrayPeaks, pointNumber, myCursor, myDb)
    pointNumber = writeToDB(secondPointArrayPeaks, pointNumber, myCursor, myDb)
    pointNumber = writeToDB(thirdPointArrayPeaks, pointNumber, myCursor, myDb)
    pointNumber = writeToDB(fourthPointArrayPeaks, pointNumber, myCursor, myDb)
    pointNumber = writeToDB(fifthPointArrayPeaks, pointNumber, myCursor, myDb)