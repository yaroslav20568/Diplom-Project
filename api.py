from flask import Flask
from flask import jsonify
from flask import request

import os
import shutil
import base64

from PIL import Image
import io
import pymysql
import datetime

from modules.main import main


app = Flask(__name__)

myDb = pymysql.connect(
	host='127.0.0.1',
	user='root',
	database='db',
	passwd='root'
)
myCursor = myDb.cursor()


def clearImgDirectory(path):
	dirSamples = path
	if(os.path.isdir(dirSamples)):
		shutil.rmtree(dirSamples)
	os.mkdir(dirSamples)

def get_characteristicsFromDB():
	myCursor.execute("SELECT * FROM characteristics;")
	rows = myCursor.fetchall()
	characteristics = []
	for row in rows:
		characteristics.append({'idCharacteristic': row[0], 'textInfo': row[1], 'waveNumber': row[2], 'intensity': row[3], 'uniq': row[4]})
	return characteristics 

def saveFilesInDirectory(files, arrayToSave):
	for file in files:
		file.save(os.path.join('D:/RROJECT/DiplomProject/server/img/samples/', file.filename))
		arrayToSave.append(f'img/samples/{file.filename}')	

@app.route('/files', methods=['POST'])
def data_processing():
	firstPathFiles = []
	secondPathFiles = []
	firstFiles = request.files.getlist('firstFiles')
	secondFiles = request.files.getlist('secondFiles')
	firstAgeCells = request.values['firstAgeCells']
	secondAgeCells = request.values['secondAgeCells']

	clearImgDirectory('D:/RROJECT/DiplomProject/server/img/samples/')
	clearImgDirectory('D:/RROJECT/DiplomProject/server/img/visualization_graphs/')
	
	# for file in firstFiles:
	# 	file.save(os.path.join('D:/RROJECT/DiplomProject/server/img/samples/', file.filename))
	# 	firstPathFiles.append(f'img/samples/{file.filename}')
	saveFilesInDirectory(firstFiles, firstPathFiles)
	saveFilesInDirectory(secondFiles, secondPathFiles)

	# for file in secondFiles:
	# 	file.save(os.path.join('D:/RROJECT/DiplomProject/server/img/samples/', file.filename))
	# 	secondPathFiles.append(f'img/samples/{file.filename}')

	myCursor.execute(f"INSERT INTO characteristics(textInfo) VALUES('{datetime.datetime.now()}');")
	myDb.commit()

	p, textStatistics = main(firstAgeCells, secondAgeCells, firstPathFiles, secondPathFiles, myCursor, myDb)

	arrayImages = []
	for filename in os.listdir('img/visualization_graphs/'):
		pil_img = Image.open(f"img/visualization_graphs/{filename}", mode='r')
		byte_arr = io.BytesIO()
		pil_img.save(byte_arr, format='PNG')
		encoded_img = base64.encodebytes(byte_arr.getvalue()).decode('ascii')
		arrayImages.append(encoded_img)

	characteristics = get_characteristicsFromDB()
	return jsonify({'arrayImages': arrayImages, 'statistics': {'p': p, 'textStatistics': textStatistics}, 'characteristics': characteristics})


@app.route('/data')
def get_data():
	characteristics = get_characteristicsFromDB()
	return jsonify({'characteristics': characteristics})


if __name__ == "__main__":
	app.run(debug=True, port=5000);