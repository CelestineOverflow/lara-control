import * as THREE from 'three';
import Koa from 'koa';
import Router from 'koa-router';
import bodyParser from 'koa-bodyparser';
import cors from '@koa/cors';
import { createServer } from 'http';
import { SerialPort } from 'serialport';
import { ReadlineParser } from '@serialport/parser-readline';
import socketIOClient from 'socket.io-client';
import Server from "socket.io";

const httpServer = createServer();
const LOCAL_IP = '192.168.2.209';
const PORT = 8081;
const PORT2 = 8082;
const app = new Koa();
const router = new Router();
let socket;

const translation = new THREE.Vector3(0, 0, 0);
const rotation = new THREE.Quaternion(0, 0, 0, 1);

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

   socket.on("Cartesian_Pose", (data) => {
      translation.set(data.X, data.Y, data.Z);
      rotation.set(data._X, data._Y, data._Z, data._W);
   });
   socket.on("heartbeat_check", (data) => {
      socket.emit("heartbeat_response", true);
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

let moveUntilPressureFlag = false; 
let KeepPressureFlag = false;
let MAX_FORCE = 10000;         // Maximum force limit
let currentForce = 0.0;          // Measured force
const kp = 0.00001;                  // Proportional gain
const ki = 0.00000;                 // Integral gain
const kd = 0.0000;                  // Derivative gain
let integral = 0.0;              // Integral accumulator
let prevError = 0.0;             // Previous step error
let lastTime = Date.now();       // Timestamp of last loop iteration
let counter = 0;
let targetForce = 1000.0;        // Desired force


async function moveRelativeZ(){
   const euler = new THREE.Euler(0, 0, 0, 'XYZ');
   euler.setFromQuaternion(rotation);
   console.log("euler:", euler.x, euler.y, euler.z);
   socket.emit('CartesianGotoManual', {
      "x": translation.x,
      "y": translation.y,
      "z": translation.z + 0.001,
      "a": euler.z,
      "b": euler.y,
      "c": euler.x,
      "status": true,
      "joint": false,
      "cartesian": true,
      "freedrive": false,
      "button": false,
      "slider": false,
      "goto": true,
      "threeD": false,
      "reference": "Base",
      "absrel": "Absolute"
   })
   await new Promise(res => setTimeout(res, 1000));
   socket.emit('CartesianGotoManual', {
		"x": 0,
		"y": 0,
		"z": 0,
		"a": 0,
		"b": 0,
		"c": 0,
		"status": false,
		"joint": false,
		"cartesian": false,
		"freedrive": false,
		"button": false,
		"slider": false,
		"goto": false,
		"threeD": false,
		"reference": "Base",
		"absrel": "Absolute"
	})
}

function PIDController() {
   const now = Date.now();
   const dt = (now - lastTime) / 1000;  // seconds
   lastTime = now;

   const error = ((targetForce - currentForce)) * -1;
   integral += error * dt;
   // Clamp integral to prevent windup
   integral = Math.max(-1000, Math.min(1000, integral));
   const derivative = dt > 0 ? (error - prevError) / dt : 0;
   prevError = error;
   let controlSignal = kp * error + ki * integral + kd * derivative ;
   // clamp control signal to [-1, 1]
   controlSignal = Math.max(-1, Math.min(1, controlSignal));
   if (Math.abs(controlSignal) < 0.1) {
      stopMovementSlider(0, 0, 0, 0, 0, 0, 'Absolute', 'Base');
      if (moveUntilPressureFlag) {
         counter++;
         if (counter > 1000) {
            moveUntilPressureFlag = false;
            counter = 0;
            console.log("Stopping moveUntilPressureFlag after 1000 iterations.");
         }
      }
   }
   else {
      startMovementSlider(0, 0, controlSignal, 0, 0, 0, 'Absolute', 'Base');
   }
   console.log("currentForce:", currentForce, "controlSignal:", controlSignal);
}



//jog.js
// const { spawn } = require('child_process');
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const jog = spawn(process.execPath, [
   path.join(path.dirname(__filename), 'jog.js'),
], {
   detached: false,
   stdio: ['ignore', 'pipe', 'pipe'],
});



jog.stdout.on('data', (data) => {
   console.log(`jog stdout: ${data}`);
});
jog.stderr.on('data', (data) => {
   console.error(`jog stderr: ${data}`);
});

// ——— MIDDLEWARES ———

const io = new Server(httpServer, {
   
 });
io.origins((origin, callback) => {
   callback(null, true);
});
io.on("connection", (socket) => {
   console.log(`Socket connected: ${socket.id}`);
});

httpServer.listen(PORT, LOCAL_IP, () => {
   console.log(`Socket.IO server listening on http://${LOCAL_IP}:${PORT}`);
});
app.use(cors({ origin: '*' }));
app.use(bodyParser());
// ——— SERIAL PORT SETUP ———
const dev = new SerialPort({ path: 'COM13', baudRate: 115200 });
const parser = dev.pipe(new ReadlineParser({ delimiter: '\n', encoding: 'utf8' }));
let pressure = 0;
let stop_Sent = false;
let temperatureObj = null;
parser.on('data', line => {
   line = line.trim();
   if (!line) return;
   try {
      const parsed = JSON.parse(line);
      if (parsed.pump_sensor) pressure = parsed.pump_sensor;
      if (parsed.temperature) temperatureObj = parsed.temperature;
      if (parsed.force) {
         currentForce = parsed.force;
         if (currentForce > MAX_FORCE) {
            if (socket) {
               if (!stop_Sent) {
                  console.log('Force exceeded max limit, stopping arm');
                  stop_Sent = true;
                  socket.emit("PowerOnOff", {
                     robotStatus: false,
                  });
               }
            }
         }
         else {
            stop_Sent = false;
            if(KeepPressureFlag || moveUntilPressureFlag) {
               PIDController();
            }
         }
      }
      io.emit('serialData', parsed);
   }
   catch (err) {
      console.error('Serial parse error:', err.message);
   }
});
parser.on('error', err => console.error('Serial parser error:', err.message));
// ——— ROUTES ———
router
   .get('/test', ctx => {
      moveRelativeZ();
      ctx.body = 'Test route!';
   })
   .get('/', ctx => {
      ctx.body = 'Hello World!';
   })
   .post('/tare', ctx => {
      dev.write('{"tare":1}\n');
      ctx.body = { success: true };
   })
   .post('/togglePump', ctx => {

      //fetch(`http://192.168.2.209:8082/togglePump?boolean=${bool}`
      let pumpState = ctx.query.boolean; //boolean
      //Pump state: { boolean: 'false' }
      if (pumpState !== 'false' && pumpState !== 'true') {
         ctx.status = 400;
         ctx.body = { error: 'pumpState must be true or false' };
         return;
      }
      pumpState = pumpState === 'true' ? 100 : 0;
      dev.write(`{"pump":${pumpState}}\n`);
      console.log('Pump written:', pumpState);
      ctx.body = { success: true, pumpState };
   })
   .post('/setBrightness', ctx => {
      const brightness = Number(ctx.query.brightness);
      if (isNaN(brightness) || brightness < 0 || brightness > 255) {
         ctx.status = 400;
         ctx.body = { error: 'Brightness must be a number between 0 and 255' };
         return;
      }
      dev.write(`{"brightness":${brightness}}\n`);
      ctx.body = { success: true, brightness };
   })
   .get('/current_pump_pressure', ctx => {
      console.log('Current pump pressure:', pressure);
      ctx.body = { pressure };
   })
   .post('/setHeater', ctx => {
      console.log('Setting heater...');
      const setTemp = Number(ctx.query.setTemp);
      if (isNaN(setTemp) || setTemp < 0 || setTemp > 250) {
         ctx.status = 400;
         ctx.body = { error: 'setTemp must be a number between 0 and 250' };
         return;
      }
      console.log('Set heater to:', setTemp);
      dev.write(`{"setTemp":${setTemp}}\n`);
      ctx.body = { success: true, setTemp };
   })
   .post('/moveUntilPressure', async ctx => {
      MAX_FORCE = 10000;
      console.log('Setting force...');
      //all query params
      console.log(ctx.query);
      //{ pressure: '5000', wiggle_room: '200' }
      const force = Number(ctx.query.pressure);
      const wiggle_room = Number(ctx.query.wiggle_room);
      if (isNaN(force) || force < 0 || force > 10000) {
         ctx.status = 400;
         console.log('Force error:', force);
         ctx.body = { error: 'pressure must be a number between 0 and 10000' };
         return;
      }
      if (isNaN(wiggle_room) || wiggle_room < 0 || wiggle_room > 10000) {
         ctx.status = 400;
         console.log('Wiggle room error:', wiggle_room);
         ctx.body = { error: 'wiggle_room must be a number between 0 and 10000' };
         return;
      }
      targetForce = force;
      moveUntilPressureFlag = true;
      while (moveUntilPressureFlag) {
         await new Promise(res => setTimeout(res, 200));
      }
      ctx.body = { success: true, force };
   }) 
   .post('/wait_for_temperature', async ctx => {
      console.log('Waiting for temperature...');
      const newHeat = Number(ctx.query.setTemp);
      if (isNaN(newHeat) || newHeat < 0 || newHeat > 250) {
         ctx.status = 400;
         ctx.body = { error: 'setTemp must be a number between 0 and 250' };
         return;
      }
      // send setTemp
      dev.write(`{"setTemp":${newHeat}}\n`);
      const timeoutMs = 5 * 60 * 1000;
      const start = Date.now();
      while (true) {
         if (temperatureObj && typeof temperatureObj.current === 'number') {
            const current = temperatureObj.current;
            console.log(`Current temperature: ${current}`);
            if (Math.abs(current - newHeat) < 1) {
               console.log('Temperature reached');
               return ctx.body = { success: 'Temperature reached' };
            }
         }
         if (Date.now() - start > timeoutMs) {
            console.log('Timeout waiting for temperature');
            dev.write('{"setTemp":0}\n');
            ctx.status = 504; // Gateway Timeout
            return ctx.body = { error: 'Timeout waiting for temperature' };
         }
         // non-blocking sleep 1s
         await new Promise(res => setTimeout(res, 1000));
      }
   }

   );
// mount router
app
   .use(router.routes())
   .use(router.allowedMethods());

app.listen(PORT2, LOCAL_IP);






