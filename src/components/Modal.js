import React from 'react';
import Loader from './Loader';

function Modal({ characteristics, setModalIsOpen, isLoading }) {
	return (
		<div className="modal" onClick={() => setModalIsOpen(false)}>
			<div className="modal__dialog">
				<div className="modal__content" onClick={(e) => e.stopPropagation()}>
					<span className="modal__close" onClick={() => setModalIsOpen(false)}>X</span>

					{isLoading ? 
						<Loader /> :
					!characteristics.length ?
						'База данных пустая' :
						<>
							<table>
								<thead>
									<tr>
										<th></th>
										<th>Волн. число</th>
										<th>Интенсивность</th>
										<th>Уник. значение</th>
									</tr>
								</thead>
								<tbody>
									{
										characteristics.length ? characteristics.map(characteristic => 
											<tr>
												{characteristic['textInfo'] ? <th>{characteristic['textInfo']}</th> : <th></th>}
												{characteristic['waveNumber'] ? <td>{characteristic['waveNumber']}</td> : <td></td>}
												{characteristic['intensity'] ? <td>{characteristic['intensity']}</td> : <td></td>}
												{characteristic['uniq'] !== null ? <td>{characteristic['uniq'] ? 'Правда' : 'Ложь'}</td> : <td></td>}
											</tr>
										) : 'no characteristics'
									}
								</tbody>
							</table>
						</>}
					
				</div>
			</div>
		</div>
	)
}

export default Modal;