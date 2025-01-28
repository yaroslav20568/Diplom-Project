import React, { useState } from 'react';
import axios from 'axios';
import Modal from './components/Modal';
import Loader from './components/Loader';
import './sass/styles.sass';

function App() {
	const [firstAgeCells, setFirstAgeCells] = useState('');
	const [secondAgeCells, setSecondAgeCells] = useState('');
	const [firstFiles, setFirstFiles] = useState([]);
	const [secondFiles, setSecondFiles] = useState([]);
	
	const [images, setImages] = useState([]);
	const [statistics, setStatistics] = useState('');
	const [characteristics, setCharacteristics] = useState([]);
	const [isLoading, setIsLoading] = useState(false);

	const [validateText, setValidateText] = useState('');
	const [modalIsOpen, setModalIsOpen] = useState(false);

	const [prevFirstAgeCells, setPrevFirstAgeCells] = useState('');
	const [prevSecondAgeCells, setPrevSecondAgeCells] = useState('');

	// const handleFirstFiles = (e) => {
	// 	setFirstFiles(e.target.files);
	// 	console.log(e.target.files);
	// };

	// const handleSecondFiles = (e) => {
	// 	setSecondFiles(e.target.files);
	// 	console.log(e.target.files);
	// };

	const sendFiles = (e) => {
		if(firstAgeCells && secondAgeCells.length && firstFiles.length && secondFiles.length) {
			e.preventDefault();
			let formData = new FormData();

			formData.append('firstAgeCells', firstAgeCells);
			formData.append('secondAgeCells', secondAgeCells);

			Array.from(firstFiles).forEach(file => {
				formData.append('firstFiles', file);
			});
			Array.from(secondFiles).forEach(file => {
				formData.append('secondFiles', file);
			});

			setIsLoading(true);
			setValidateText('');
			axios.post('/files', formData, {headers: {"Content-Type": "multipart/form-data"}})
				.then(({data}) => {
					setImages(data['arrayImages']);
					setStatistics(data.statistics);
					setCharacteristics(data.characteristics);
					setIsLoading(false);

					setPrevFirstAgeCells(firstAgeCells);
					setPrevSecondAgeCells(secondAgeCells);

					setFirstAgeCells('');
					setSecondAgeCells('');
					setFirstFiles([]);
					setSecondFiles([]);
				})
		} else {
			setValidateText('Заполните все инпуты');
		}
	};

	const getCharacteristicsFromDB = () => {
		setModalIsOpen(true);
		if(!characteristics.length) {
			setIsLoading(true);
			axios.get('/data')
				.then(({data}) => {
					setCharacteristics(data.characteristics);
					setIsLoading(false);
				})
		}		
	};

	function sliceIntoChunks(arr, chunkSize) {
		const res = [];
		for (let i = 0; i < arr.length; i += chunkSize) {
			const chunk = arr.slice(i, i + chunkSize);
			res.push(chunk);
		}
		return res;
	};

	function cutArray(arr) {
		const firstImages = arr.slice(0, arr.length / 2);
		const secondImages = arr.slice(arr.length / 2, arr.length);

		return { firstImages, secondImages };
	};

	const newImages = sliceIntoChunks(images, 5);
	const { firstImages, secondImages } = cutArray(newImages);

	return (
		<div className="app">
			<div className="control-ui">
				<div className="control-ui__top">
					<div className="control-ui__main-title">Статистика раковых клеток</div>
					<button 
						className="btn btn--primary control-ui__btn"
						onClick={getCharacteristicsFromDB}
						disabled={isLoading}
					>
						Посмотреть информацию о пиках
					</button>
				</div>
				
				<div className="control-ui__title">1-й объект(раковые клетки)</div>
				<input
					type="text"
					value={firstAgeCells}
					onInput={(e) => setFirstAgeCells(e.target.value)}
					placeholder="Введите возраст раковых клеток"
					className="input__text"
				/>

				<div className="input-file__wrapper">
					<input
						type="file"
						multiple="multiple"
						onChange={e => setFirstFiles(e.target.files)}
						id="firstFiles"
						className="input-file__real"
					/>

					<label htmlFor="firstFiles" className="input-file__fake">
						<span>Загрузите образцы раковых клеток</span>
					</label>
				</div>

				<div className="control-ui__title">2-й объект(раковые клетки)</div>
				<input
					type="text"
					value={secondAgeCells}
					onInput={(e) => setSecondAgeCells(e.target.value)}
					placeholder="Введите возраст раковых клеток"
					className="input__text"
				/>

				<div className="input-file__wrapper">
					<input
						type="file"
						multiple="multiple"
						onChange={e => setSecondFiles(e.target.files)}
						id="secondFiles"
						className="input-file__real"
					/>

					<label htmlFor="secondFiles" className="input-file__fake">
						<span>Загрузите образцы раковых клеток</span>
					</label>
				</div>

				<div className="validate__text">{validateText}</div>

				<button
					onClick={sendFiles} 
					className="btn btn--yellow"
					disabled={isLoading}
				>
					Сделать статистику
				</button>
			</div>
			
			
		{isLoading ? 
			<Loader /> :
		!images.length ?
			'' :
			<>
				<div className="statistics">
					<div>p: {statistics.p}</div>
					<div>{statistics.textStatistics}</div>
				</div>

				<div className="images-list">
					{firstImages.map((images, index) => 
						<div>
							{images.map((img, i) => 
								<>	
									<div>1-й объект(раковые клетки с возрастом {prevFirstAgeCells})</div>
									<div>{index + 1}-й образец</div>
									<div>{i + 1}-я точка</div>
									<img src={`data:image/jpeg;base64,${img}`} alt="img_data" />
								</>
							)}
						</div>
					)}

					{secondImages.map((images, index) => 
						<div>
							{images.map((img, i) => 
								<>	
									<div>2-й объект(раковые клетки с возрастом {prevSecondAgeCells})</div>
									<div>{index + 1}-й образец</div>
									<div>{i + 1}-я точка</div>
									<img src={`data:image/jpeg;base64,${img}`} alt="img_data" />
								</>
							)}
						</div>
					)}
				</div>
			</>}

			{modalIsOpen && 
				<Modal
					characteristics={characteristics}
					setModalIsOpen={setModalIsOpen}
					isLoading={isLoading}
				/>}
		</div>
	);
}

export default App;
