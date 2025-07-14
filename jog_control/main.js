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
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import Writer from './writer.js';

const MAX_BYTES = 1024 * 1024 * 100; // 100 MB
let bytesLogged = 0;
let writer;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
let recording = false;
let not_finished_recording = true;

const httpServer = createServer();
const LOCAL_IP = '192.168.2.209';
const PORT = 8081;
const PORT2 = 8082;
const app = new Koa();
const router = new Router();
let socket;
const deltaTranslation = new THREE.Vector3(0, 0, 0);
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
      deltaTranslation.set(translation.x - data.X, translation.y - data.Y, translation.z - data.Z);
      translation.set(data.X, data.Y, data.Z);
      rotation.set(data._X, data._Y, data._Z, data._W);
      
   });
   socket.on("heartbeat_check", (data) => {
      socket.emit("heartbeat_response", true);
   });


}
setupSocket();

let moveUntilPressureFlag = false;
let KeepPressureFlag = false;
let currentForce = 0.0;          // Measured force
const kp = 0.0001;                  // Proportional gain
// const kp = 0.0002;                  // Proportional gain
const ki = 0.0;                 // Integral gain
const kd = 0;                  // Derivative gain
let integral = 0.0;              // Integral accumulator
let prevError = 0.0;             // Previous step error
let lastTime = Date.now();       // Timestamp of last loop iteration
let counter = 0;
let targetForce = 1000.0;

const DEFAULT_MAX_FORCE = 1000;
const ONPRESS_MAX_FORCE = 12000;
let reset_MAX_FORCE = false;
let MAX_FORCE = DEFAULT_MAX_FORCE;

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


async function smallMove() {
   //we move up in z 10 times 
   for (let i = 0; i < 10; i++) {
      startMovementSlider(0, 0, 0.01, 0, 0, 0, "Absolute", "Base");
   }
   await stopMovementSlider(0, 0, 0, 0, 0, 0, "Absolute", "Base");
   console.log("Small move done");
}

async function moveRelativeZ(z_value_milimeters) {
   // console.log("Moving relative Z:", z_value_milimeters);
   const z_value = z_value_milimeters / 1000; // Convert to meters
   const newTranslation = new THREE.Vector3(0, 0, 0 + z_value);
   socket.emit('CartesianGotoManual', {
      "x": newTranslation.x,
      "y": newTranslation.y,
      "z": newTranslation.z,
      "a": 0,
      "b": 0,
      "c": 0,
      "status": true,
      "joint": false,
      "cartesian": true,
      "freedrive": false,
      "button": false,
      "slider": false,
      "goto": true,
      "threeD": false,
      "reference": "Base",
      "absrel": "Relative"
   })
   await new Promise(resolve => setTimeout(resolve, 50)); // Wait for 1 second
}
async function stopRelative() {
   await socket.emit('CartesianGotoManual', {
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

let ONESHOOT_COUNTER = 0;
let WAITING_FOR_ONE_SHOOT = false;
let lock_counter = 100;
let lock = false;
async function oneShootPressure() {
   console.log(deltaTranslation.z, "Delta Z translation");
   if(Math.abs(deltaTranslation.z) < 0.00002){
      console.log("Delta Z translation is too small");
      lock_counter--;
      if (lock_counter < 0) {
         lock = true;
         lock_counter = 100;
      }
      if (lock) {
         await smallMove();
         console.log("Delta Z translation is too small, skipping oneShootPressure");
         WAITING_FOR_ONE_SHOOT = false;
         lock = false;
         return;
      }
   }
   else{
      lock = false;
      lock_counter = 100;
   }


   let error = currentForce - targetForce;
   let controlSignal = kp * error + ki * integral + kd * (error - prevError) / (Date.now() - lastTime);
   controlSignal = Math.max(-0.1, Math.min(controlSignal, 0.1));

   await moveRelativeZ(controlSignal);
   // 0.000543629999999996
   if (controlSignal < 0.01 && controlSignal > -0.01 && !KeepPressureFlag) {
      ONESHOOT_COUNTER++;
      lock_counter = 100;
      lock = false;
      console.log("Control signal is small, incrementing counter:", ONESHOOT_COUNTER);
      if (ONESHOOT_COUNTER > 50) {
         ONESHOOT_COUNTER = 0;
         moveUntilPressureFlag = false;
         await stopRelative();
      }
   }
   WAITING_FOR_ONE_SHOOT = false;
}



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
const dev = new SerialPort({ path: 'COM4', baudRate: 115200 });
//send connected message to serial port
dev.on('open', () => {
   console.log('Serial port opened');
   dev.write('{"connected":true}\n');
});
const parser = dev.pipe(new ReadlineParser({ delimiter: '\n', encoding: 'utf8' }));
let pressure = 0;
let stop_Sent = false;
let temperatureObj = null;
let lastTimeReport = Date.now();
const reportInterval = 32; // 1 second
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
            if (moveUntilPressureFlag || KeepPressureFlag) {
               if (!WAITING_FOR_ONE_SHOOT) {
                  WAITING_FOR_ONE_SHOOT = true;
                  oneShootPressure();
               }
            }
         }
         if (reset_MAX_FORCE && currentForce < DEFAULT_MAX_FORCE / 2) {
            console.log("Resetting MAX_FORCE to default value.");
            MAX_FORCE = DEFAULT_MAX_FORCE;
            reset_MAX_FORCE = false;
         }
         if (recording && writer) {
            const data = JSON.stringify(parsed) + '\n';
            writer.write(data);
            bytesLogged += Buffer.byteLength(data, 'utf8');
            if (bytesLogged >= MAX_BYTES) {
               console.log('Max file size reached, stopping recording.');
               writer.end();
               recording = false;
            }

         }
         
      }
      
      if (Date.now() - lastTimeReport > reportInterval) {
         lastTimeReport = Date.now();
         io.emit('serialData', parsed);
      }
   }
   catch (err) {
      console.error('Serial parse error:', err.message);
   }
});
parser.on('error', err => console.error('Serial parser error:', err.message));
// ——— ROUTES ———
router
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
      console.log('Pump state:', pumpState);
      pumpState = pumpState.toLowerCase();
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
   .post('/startRecording', ctx => {
      if (recording) {
         ctx.body = { success: false, message: 'Already recording' };
         return;
      }
      recording = true;
      bytesLogged = 0;
      writer = new Writer(path.join(__dirname, 'recording.txt'));
      ctx.body = { success: true, message: 'Recording started' };
   }
   )
   .post('/stopRecording', async ctx => {
      if (!recording) {
         ctx.body = { success: false, message: 'Not recording' };
         return;
      }
      recording = false;
      ctx.body = { success: true, message: 'Recording stopped' };
   }) 
   .get('/getRecording', ctx => {
      const filePath = path.join(__dirname, 'recording.txt');
      ctx.attachment(filePath);
      ctx.body = fs.createReadStream(filePath);
   }

   )
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
      console.log('Set heater:', setTemp);
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
      // await smallMove();
      MAX_FORCE = ONPRESS_MAX_FORCE;
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
      if(io){
         io.emit('forceUpdate', { force });
      }
      moveUntilPressureFlag = true;
      KeepPressureFlag = false;
      while (moveUntilPressureFlag) {
         await new Promise(res => setTimeout(res, 200));
      }
      reset_MAX_FORCE = true;
      console.log('Force set:', force);
      ctx.body = { success: true, force };
   })
   .post('/keepForce', async ctx => {
      MAX_FORCE = ONPRESS_MAX_FORCE;
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
      KeepPressureFlag = true;
      ctx.body = { success: true, force };
   }
   )
   .post('/stopKeepForce', async ctx => {
      console.log('Stopping keep force...');
      KeepPressureFlag = false;
      reset_MAX_FORCE = true;
      ctx.body = { success: true };
   }
   )
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






