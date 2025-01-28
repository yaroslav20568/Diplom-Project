from modules.functions import getResultsFromImg
from scipy.stats import kruskal

def imgsProcessing(imgArray, ageCells, myCursor, myDb):
	waveNumberArray = []
		
	myCursor.execute(f"INSERT INTO characteristics(textInfo) VALUES('Раковые клетки с возрастом {ageCells}');")
	myDb.commit()
		
	for i, img in enumerate(imgArray):
		getResultsFromImg(img, i + 1, waveNumberArray, myCursor, myDb)
		
	return waveNumberArray	

def main(firstAgeCells, secondAgeCells, firstPathFiles, secondPathFiles, myCursor, myDb):
	firstWaveNumberArray = imgsProcessing(firstPathFiles, firstAgeCells, myCursor, myDb)
	secondWaveNumberArray = imgsProcessing(secondPathFiles, secondAgeCells, myCursor, myDb)

	_, p = kruskal(firstWaveNumberArray, secondWaveNumberArray)

	textStatistics = ''

	alpha = 0.05
	if p > alpha:
		print('Примеры распределений равны')
		textStatistics = 'Примеры распределений равны'
	else:
		print('Примеры распределений не равны')
		textStatistics = 'Примеры распределений не равны'

	return p, textStatistics