const socketIOClient = require('socket.io-client');
const { WebSocketServer } = require('ws');
let socket;
function setupSocket() {
 socket = socketIOClient("http://192.168.2.13:8081");
 socket.on("connect", async () => {
   console.log(`Connected with socket ID: ${socket.id}`);
   console.log("Connected and emitted events.");
 });
 socket.on("heartbeat_check", () => {
   socket.emit("heartbeat_response", true);
 });
 socket.on("connect_error", (err) => {
   console.error(`Connection error due to ${err.message}`);
 });
 socket.on("disconnect", (reason) => {
   console.log(`Disconnected: ${reason}`);
 });
 socket.on("error", (error) => {
   console.error("Socket error:", error);
 });
}
// Modified to accept absrel and reference parameters
function startMovementSlider(q0, q1, q2, q3, q4, q5, absrel, reference) {
 let data = {
   q0: q0,
   q1: q1,
   q2: q2,
   q3: q3,
   q4: q4,
   q5: q5,
   status: true,
   joint: false,
   cartesian: true,
   freedrive: false,
   button: false,
   slider: true,
   goto: false,
   threeD: false,
   reference: reference || "Base",
   absrel: absrel || "Absolute",
 };
 socket.emit("CartesianSlider", data);
}
// Modified to accept absrel and reference parameters
function stopMovementSlider(q0, q1, q2, q3, q4, q5, absrel, reference) {
 let data = {
   q0: q0,
   q1: q1,
   q2: q2,
   q3: q3,
   q4: q4,
   q5: q5,
   status: false,
   joint: false,
   cartesian: true,
   freedrive: false,
   button: false,
   slider: true,
   goto: false,
   threeD: false,
   reference: reference || "Base",
   absrel: absrel || "Absolute",
 };
 socket.emit("CartesianSlider", data);
}
setupSocket();
let moveInterval = null;
let currentAbsrel = "Absolute";
let currentReference = "Base";
// New function to start movement using all six axis values
function startMovingAll(q0, q1, q2, q3, q4, q5, absrel, reference) {
 if (moveInterval === null) {
   // Save the current reference settings
   currentAbsrel = absrel || "Absolute";
   currentReference = reference || "Base";
   startMovementSlider(q0, q1, q2, q3, q4, q5, currentAbsrel, currentReference);
   moveInterval = setInterval(() => {
     startMovementSlider(q0, q1, q2, q3, q4, q5, currentAbsrel, currentReference);
   }, 10);
 }
}
function stopMoving() {
 if (moveInterval !== null) {
   clearInterval(moveInterval);
   moveInterval = null;
   stopMovementSlider(0, 0, 0, 0, 0, 0, currentAbsrel, currentReference);
 }
}
let movementTimeout = null;
function resetMovementTimeout() {
 if (movementTimeout) clearTimeout(movementTimeout);
 movementTimeout = setTimeout(() => {
   stopMoving();
   movementTimeout = null;
   console.log("Movement timeout reached");
 }, 200);
}

let current_values = [0, 0, 0, 0, 0, 0];

function setupWebSocketServer() {
   // Get local IP address
   const os = require('os');
   const ifaces = os.networkInterfaces();
   let localIp = "192.168.2.209";
   // host="192.168.2.209";
   const wss = new WebSocketServer({ port: 8082, host: localIp });
   console.log(`WebSocket server started on ws://${localIp}:8082`);
   wss.on("connection", (ws) => {
      // Create a timeout variable for this connection
      let movementTimeout = null;
      ws.on("message", (data) => {
         try {
            const message = JSON.parse(data.toString());
            console.log("Received message:", message);
            if (message.command === "echo") {
               ws.send(JSON.stringify({
                  status: "echo",
                  message: message.message || "Echo received",
                  timestamp: new Date().toISOString()
               }));
            } else if (message.command === "startMoving") {
               //example json with all fields
               //{"command":"startMoving","q0":0,"q1":0,"q2":0,"q3":0,"q4":0,"q5":0,"absrel":"Absolute","reference":"Base"}
               resetMovementTimeout();
               // Expect all six axis values (q0...q5) to be provided
               if (
                  typeof message.q0 === 'number' &&
                  typeof message.q1 === 'number' &&
                  typeof message.q2 === 'number' &&
                  typeof message.q3 === 'number' &&
                  typeof message.q4 === 'number' &&
                  typeof message.q5 === 'number'
               ) {
                  // If the new values are different from current_values, send a stop movement beforehand
                  if (
                     message.q0 !== current_values[0] ||
                     message.q1 !== current_values[1] ||
                     message.q2 !== current_values[2] ||
                     message.q3 !== current_values[3] ||
                     message.q4 !== current_values[4] ||
                     message.q5 !== current_values[5]
                  ) {
                     stopMoving();
                  }
                  // Update current_values with new values
                  current_values = [message.q0, message.q1, message.q2, message.q3, message.q4, message.q5];

                  let absrel = (message.absrel === "Absolute" || message.absrel === "Relative") ? message.absrel : "Absolute";
                  // Default reference is "Base" it can be "Tool" 
                  let reference = message.reference || "Base";
                  startMovingAll(message.q0, message.q1, message.q2, message.q3, message.q4, message.q5, absrel, reference);
                  ws.send(JSON.stringify({
                     status: "started",
                     q0: message.q0,
                     q1: message.q1,
                     q2: message.q2,
                     q3: message.q3,
                     q4: message.q4,
                     q5: message.q5,
                     absrel: absrel,
                     reference: reference
                  }));
               } else {
                  ws.send(JSON.stringify({ error: "Invalid axis values" }));
               }
            } else if (message.command === "stopMoving") {
               stopMoving();
               ws.send(JSON.stringify({ status: "stopped" }));
            } else {
               ws.send(JSON.stringify({ error: "Unknown command" }));
            }
         } catch (error) {
            ws.send(JSON.stringify({ error: "Invalid JSON" }));
         }
      });
      ws.on("close", () => {
         if (movementTimeout) clearTimeout(movementTimeout);
      });
   });
}
setupWebSocketServer();