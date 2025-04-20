/**
 * GCS API
 * 
 * Receives data from the API and loads it into memory to be accessed by other javascript modules.
 *
 * Functions and constants should be prefixed with "api_"  
 */

let api_socket;
let api_latest = {};

function connectSocket() {
	api_socket = new WebSocket("ws://localhost:1887");

	api_socket.onopen = () => {
		console.log("connection gaming");
	};

	api_socket.onmessage = (event) => {
		try {
			const api_data = JSON.parse(event.data);
			api_latest = api_data;
			if (api_latest.id == 3) {
				interface_updateValue("av-vel-total", api_latest.data.velocity);
				interface_updateValue("av-accel-x-lo", api_latest.data.accelLowX);
				interface_updateValue("av-accel-y-lo", api_latest.data.accelLowY);
				interface_updateValue("av-accel-z-lo", api_latest.data.accelLowZ);
				interface_updateValue("av-accel-x-hi", api_latest.data.accelHighX);
				interface_updateValue("av-accel-y-hi", api_latest.data.accelHighY);
				interface_updateValue("av-accel-z-hi", api_latest.data.accelHighZ);
				interface_updateValue("av-gyro-x", api_latest.data.gyroX);
				interface_updateValue("av-gyro-y", api_latest.data.gyroY);
				interface_updateValue("av-gyro-z", api_latest.data.gyroZ);
			}
		}
		catch (error) {
			console.error("data is dogshit");
		}
	};

	api_socket.onerror = (error) => {
		console.error("websocket is dogshit");
	};

	api_socket.onclose = (event) => {
		console.log("socket closed");
	};
}

connectSocket();
