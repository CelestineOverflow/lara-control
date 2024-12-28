import socketIOClient from 'socket.io-client';
//very important  npm install socket.io-client@2 
//old ass version i got no control over it
const payload = {
    "A1": 1.0,
    "A2": 0,
    "A3": 0,
    "A4": 0,
    "A5": 0,
    "A6": 0
};
// Connect to the WebSocket server with authentication if required
const socket = socketIOClient('http://192.168.2.13:8081', {
});

socket.on("connect", async () => {
    console.log(`Connected with socket ID: ${socket.id}`);

    // Emitting initial events
    socket.emit('PowerStatus', { data: 'CheckPower' });
    socket.emit('check_zerog_status', { data: 'check_zerog' });
    socket.emit('isHmiButton', { hmi_button: false });
    socket.emit('SimulateReal', { data: false });
    console.log("Connected and emitted events.");

    try {
        await new Promise(resolve => setTimeout(resolve, 5000)); 
        socket.emit('JointGotoManual', {
            q0: payload.A1,
            q1: payload.A2,
            q2: payload.A3,
            q3: payload.A4,
            q4: payload.A5,
            q5: payload.A6,
            status: true,      // Assuming 'status' needs to be true to start movement
            joint: true,       // Assuming 'joint' needs to be true
            cartesian: false,
            freedrive: false,
            button: false,
            slider: false,
            goto: true,        // 'goto' might need to be true to start movement
            threeD: false,
            reference: 'nil',
            absrel: 'Absolute'
        });
        console.log("Sent 'JointGotoManual' start event.");

        // Wait for 5 seconds
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Emit the stop movement event
        socket.emit('JointGotoManual', {
            q0: payload.A1,
            q1: payload.A2,
            q2: payload.A3,
            q3: payload.A4,
            q4: payload.A5,
            q5: payload.A6,
            status: false,     // Set to false to stop movement
            joint: false,
            cartesian: false,
            freedrive: false,
            button: false,
            slider: false,
            goto: false,
            threeD: false,
            reference: 'nil',
            absrel: 'Absolute'
        });
        console.log("Sent 'JointGotoManual' stop event.");
    } catch (error) {
        console.error('Error in HTTP POST:', error);
    }
});

// Add listeners for the events
socket.on('PowerStatus', (data) => {
    console.log('Received PowerStatus:', data);
});

socket.on('check_zerog_status', (data) => {
    console.log('Received check_zerog_status:', data);
});

socket.on('isHmiButton', (data) => {
    console.log('Received isHmiButton:', data);
});

socket.on('SimulateReal', (data) => {
    console.log('Received SimulateReal:', data);
});

// // Add a listener for any event to debug
// socket.onAny((eventName, ...args) => {
//     console.log(`Received event '${eventName}':`, args);
// });

socket.on("connect_error", (err) => {
    console.error(`Connection error due to ${err.message}`);
});

socket.on("disconnect", (reason) => {
    console.log(`Disconnected: ${reason}`);
});

socket.on("error", (error) => {
    console.error('Socket error:', error);
});