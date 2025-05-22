
import socketIOClient from 'socket.io-client';
import { get, writable } from 'svelte/store';
import { toRad } from './utils';
import { autonomous_control, isPaused, loadcell_value, Pose, robotJoints, TargetPose, temperature, threshold, torques, trayPoses, unblock_pressure_flag } from '$lib/robotics/coordinate.svelte';
import { Vector3, Quaternion } from 'three';
import { error, warning } from '$lib/NotificationsLib';
//very important  npm install socket.io-client@2 --save
let isConnected = false;
export const lara_api_joint_stream = writable([0, 0, 0, 0, 0, 0]);

export const lara_robot_power_status = writable(false);
export const lara_collision_status = writable(false);
export const lara_simulated_status = writable(false); // Simulated or real robot
let socket: any;
let apiSocket: any;



// ws.onmessage = (event) => {
//         const temp = JSON.parse(event.data);
//         if (temp.hasOwnProperty("force")) {
//             loadcell_value.set(parseFloat(temp.force));
//         }
//         if (temp.hasOwnProperty("temperature")) {
//             temperature.set(temp.temperature);
//         }
//         if (temp.hasOwnProperty("is_paused")) {
//             isPaused.set(temp.is_paused);
//         }
//         if (temp.hasOwnProperty("error")) {
//             error(JSON.stringify(temp.error), 5000);
//         }
//         if (temp.hasOwnProperty("warning")) {
//             warning(JSON.stringify(temp.warning), 5000);
//         }
//         if (temp.hasOwnProperty("torques")) {
//             torques.set(temp.torques);
//         }
//         if (temp.hasOwnProperty("autonomous_control")) {
//             autonomous_control.set(temp.autonomous_control);
//         }
//         if (temp.hasOwnProperty("threshold")) {
//             threshold.set(temp.threshold);
//         }
//         if (temp.hasOwnProperty("unblock_pressure_flag")) {
//             unblock_pressure_flag.set(temp.unblock_pressure_flag);
//         }
//         data.set(temp);

export function apiSocketSetup() {
    let apiSocket = socketIOClient('192.168.2.209:8081');

    apiSocket.on('connect', async () => {
        console.log(`Connected with socket ID: ${socket.id}`);
    });

    apiSocket.on('serialData', (data : any) => {
        if (data.hasOwnProperty("force")) {
            loadcell_value.set(parseFloat(data.force));
        }
        if (data.hasOwnProperty("temperature")) {
            temperature.set(data.temperature);
        }
        if (data.hasOwnProperty("is_paused")) {
            isPaused.set(data.is_paused);
        }
        if (data.hasOwnProperty("error")) {
            error(JSON.stringify(data.error), 5000);
        }
        if (data.hasOwnProperty("warning")) {
            warning(JSON.stringify(data.warning), 5000);
        }
        if (data.hasOwnProperty("torques")) {
            torques.set(data.torques);
        }
        if (data.hasOwnProperty("autonomous_control")) {
            autonomous_control.set(data.autonomous_control);
        }
        if (data.hasOwnProperty("threshold")) {
            threshold.set(data.threshold);
        }
        if (data.hasOwnProperty("unblock_pressure_flag")) {
            unblock_pressure_flag.set(data.unblock_pressure_flag);
        }
    });
}

export function setupSocket() {
    socket = socketIOClient("http://192.168.2.13:8081");

     
    socket.on("connect", async () => {
        console.log(`Connected with socket ID: ${socket.id}`);
        isConnected = true;
        console.log("Connected and emitted events.");
        await checkPowerStatus();
        await checkCollisionStatus();
        await fetch_cartesian_pose();
        await fetch_joints_angle();
        await getTray();
        await getTargetPose();
        await getOffsetX();
    });

    socket.on("heartbeat_check", () => {
        socket.emit("heartbeat_response", true);
    });


    //42["SimulateReal",{"data":true}]
    socket.on("SimulateReal", (data: any) => {
        if (data.data === true) {
            lara_simulated_status.set(true);
        } else {
            lara_simulated_status.set(false);
        }
    });

    //42["Error","Warning Cannot initialize the robot, please press the white reset button and try again, switching to simulation mode."]
    socket.on("Error", (data: any) => {
        //check this text
        //Warning Communication Problem with GUI server! Jog Motion was stopped. Check the connection to the Teach Pendant!
        if (data.includes("Warning Communication Problem with GUI server! Jog Motion was stopped. Check the connection to the Teach Pendant!")) {
            return;
        }
        if (data.includes("Error")) {
            error(data, 5000);
            return;
        }
        if (data.includes("Warning")) {
            warning(data, 5000);
            return;
        }
        
    });

    //42["PowerStatus",{"data":"Power On"}]
    socket.on("PowerStatus", (data: any) => {
        if (data.data === "Power On") {
            lara_robot_power_status.set(true);
        } else {
            lara_robot_power_status.set(false);
        }
    });
    //42["getCollisionStatus",{"gui_collision":true}]
    socket.on("getCollisionStatus", (data: any) => {
        if (data.gui_collision == true) {
            lara_collision_status.set(false);
        } else {
            lara_collision_status.set(true);
        }
    });


    //Cartesian_Pose
    socket.on("Cartesian_Pose", (data: any) => {
        robotJoints.update((joints) => {
            const x = parseFloat(data.X);
            const y = parseFloat(data.Y);
            const z = parseFloat(data.Z);
            const a = parseFloat(data.A);
            const b = parseFloat(data.B);
            const c = parseFloat(data.C);
            const _x = parseFloat(data._X);
            const _y = parseFloat(data._Y);
            const _z = parseFloat(data._Z);
            const _w = parseFloat(data._W);
            if (!isNaN(x)) joints.x = x;
            if (!isNaN(y)) joints.y = y;
            if (!isNaN(z)) joints.z = z;
            if (!isNaN(a)) joints.a = a;
            if (!isNaN(b)) joints.b = b;
            if (!isNaN(c)) joints.c = c;
            if (!isNaN(_x)) joints._x = _x;
            if (!isNaN(_y)) joints._y = _y;
            if (!isNaN(_z)) joints._z = _z;
            if (!isNaN(_w)) joints._w = _w;
            

            return joints;
        });
    });
    //Joint_Angle
    socket.on("Joint_Angle", (data: any) => {
        robotJoints.update((joints) => {
            const joint1 = parseFloat(data.A1);
            const joint2 = parseFloat(data.A2);
            const joint3 = parseFloat(data.A3);
            const joint4 = parseFloat(data.A4);
            const joint5 = parseFloat(data.A5);
            const joint6 = parseFloat(data.A6);
            if (!isNaN(joint1) && joint1 !== undefined) joints.joint1 = joint1;
            if (!isNaN(joint2) && joint2 !== undefined) joints.joint2 = joint2;
            if (!isNaN(joint3) && joint3 !== undefined) joints.joint3 = joint3;
            if (!isNaN(joint4) && joint4 !== undefined) joints.joint4 = joint4;
            if (!isNaN(joint5) && joint5 !== undefined) joints.joint5 = joint5;
            if (!isNaN(joint6) && joint6 !== undefined) joints.joint6 = joint6;
            return joints;
        });
    });

    socket.on("connect_error", (err: { message: any }) => {
        console.error(`Connection error due to ${err.message}`);
    });

    socket.on("disconnect", (reason: any) => {
        console.log(`Disconnected: ${reason}`);
    });

    socket.on("error", (error: any) => {
        console.error("Socket error:", error);
    });
}

export function setCollisionStatus(enable: boolean) {
    const status = enable ? "on" : "off";
    socket.emit("gui_collision_status", {
        gui_collision: status,
    });
}

export function startMovementSlider(q0: any, q1: any, q2: any, q3: any, q4: any, q5: any) {
    // console.log("startMovementSlider", q0, q1, q2, q3, q4, q5);
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
        reference: "Base",
        absrel: "Absolute",
    };
    socket.emit("CartesianSlider", data);
}

//42["SimulateReal",{"data":false}]

export function simulateReal(status: boolean) {
    socket.emit("SimulateReal", {
        data: status,
    });
}

export function stopMovementSlider(q0: any, q1: any, q2: any, q3: any, q4: any, q5: any) {
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
        reference: "Base",
        absrel: "Absolute",
    };
    socket.emit("CartesianSlider", data);
}


export function startMovementCartesian(x: any, y: any, z: any) {
    // console.log("startMovementCartesian", x, y, z);
    let data = {
        x: x,
        y: -0.400,
        z: 0.286,
        a: -3.141593,
        b: 0,
        c: 3.141593,
        status: true,
        joint: false,
        cartesian: true,
        freedrive: false,
        button: false,
        slider: false,
        goto: true,
        threeD: false,
        reference: "Base",
        absrel: "Absolute",
    };
    // console.log(x, y, z);
    socket.emit("CartesianGotoManual", data);
}


//42["reset_collision",{"reset":true}]

export function resetCollision() {
    socket.emit("reset_collision", {
        reset: true,
    });
}


//42["restart_deployer",{"data":true}]
export function restartDeployer() {
    socket.emit("restart_deployer", {
        data: true,
    });
}

//42["reboot",{"data":true}]	
export function reboot() {
    socket.emit("reboot", {
        data: true,
    });
}

export function startMovement() {
    socket.emit("JointGotoManual", {
        q0: get(lara_api_joint_stream)[0],
        q1: get(lara_api_joint_stream)[1],
        q2: get(lara_api_joint_stream)[2],
        q3: get(lara_api_joint_stream)[3],
        q4: get(lara_api_joint_stream)[4],
        q5: get(lara_api_joint_stream)[5],
        status: true, // Start movement
        joint: true,
        cartesian: false,
        freedrive: false,
        button: false,
        slider: false,
        goto: true,
        threeD: false,
        reference: "nil",
        absrel: "Absolute",
    });
    // console.log("Sent 'JointGotoManual' start event.");
}

export function stopMovement() {
    socket.emit("JointGotoManual", {
        q0: get(lara_api_joint_stream)[0],
        q1: get(lara_api_joint_stream)[1],
        q2: get(lara_api_joint_stream)[2],
        q3: get(lara_api_joint_stream)[3],
        q4: get(lara_api_joint_stream)[4],
        q5: get(lara_api_joint_stream)[5],
        status: false, // Stop movement
        joint: false,
        cartesian: false,
        freedrive: false,
        button: false,
        slider: false,
        goto: false,
        threeD: false,
        reference: "nil",
        absrel: "Absolute",
    });
}



//42["PowerStatus",{"data":"CheckPower"}]

async function checkPowerStatus() {
    socket.emit("PowerStatus", {
        data: "CheckPower",
    });
}

//42["gui_collision_status",{"gui_collision":"on"}]
async function checkCollisionStatus() {
    socket.emit("gui_collision_status", {
        gui_collision: "on",
    });
}

export function powerOnOff(status: boolean) {
    socket.emit("PowerOnOff", {
        robotStatus: status,
    });
}

export async function setTray() {
    try {
        const response = await fetch("http://192.168.2.209:1442/setTray", {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        });
        console.log("Set tray response:", response);
        const data = await response.json();
        trayPoses.set([]);
        data.forEach((element: any) => {
            const pose = new Pose(
                new Vector3(element.position.x, element.position.z, -element.position.y),
                new Quaternion(element.orientation.x, element.orientation.z, -element.orientation.y, element.orientation.w)
              );
            
              trayPoses.update((poses) => {
                poses.push(pose);
                return poses;
            });
        }
        );
    }
    catch (error) {
        console.error("Error:", error);
    }
}

export async function getTray() {
    try {
        const response = await fetch("http://192.168.2.209:1442/getTray", {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        });
        const data = await response.json();
        trayPoses.set([]);
        data.forEach((element: any) => {
            const pose = new Pose(
                new Vector3(element.position.x, element.position.z, -element.position.y),
                new Quaternion(element.orientation.x, element.orientation.z, -element.orientation.y, element.orientation.w)
              );
            trayPoses.update((poses) => {
                poses.push(pose);
                return poses;
            });
        }
        );
    }
    catch (error) {
        console.error("Error:", error);
    }
}

let offsetX = 2.5;

export async function getOffsetX() {
    try {
        const response = await fetch("http://192.168.2.209:1442/getOffset", {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        });
        const data = await response.json();
        offsetX = data.offset_x;
    }
    catch (error) {
        console.error("Error:", error);
    }
    
}

export async function goToSocket() {
    const response = await fetch("http://192.168.2.209:1442/moveToSocketSmart?offset_z=0", {
        method: "POST",
        headers: {
            "accept": "application/json",
        },
    });
    const data = await response.json();
    console.log(data);
}
export async function press(force: number) {
    //force between 0 and 10000
    if (force > 10000) {
        console.error("Force too high, setting to max force.");
        force = 10000;
    }
    
    const response = await fetch(`http://192.168.2.209:8082/moveUntilPressure?pressure=${force}&wiggle_room=200`, {
        method: "POST",
        headers: {
            "accept": "application/json",
        },
    });
    const data = await response.json();
    return data;
}

export async function togglePump(bool: boolean) {
    try {
        const response = await fetch(`http://192.168.2.209:8082/togglePump?boolean=${bool}`, {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Toggle pump response:", data);
    } catch (error) {
        console.error("Error toggling pump:", error);
    }
}


export async function tare() {
    try {
        const response = await fetch(`http://192.168.2.209:1442/tare`, {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Toggle pump response:", data);
    } catch (error) {
        console.error("Error toggling pump:", error);
    }
}

export async function setSocket() {
    try {
        const response = await fetch("http://192.168.2.209:1442/setSocket", {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Set target pose response:", data);

        const pose = new Pose(
            new Vector3(data.position[0], data.position[2], -data.position[1]),
            new Quaternion(data.orientation[0], data.orientation[2], -data.orientation[1], data.orientation[3])
        );

        TargetPose.set(pose);
    } catch (error) {
        console.error("Error setting target pose:", error);
    }
}

export async function getTargetPose() {
    try {
        const response = await fetch("http://192.168.2.209:1442/getSocket", {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        });
        const data = await response.json();
        const pose = new Pose(
            new Vector3(data.position[0], data.position[2], -data.position[1]),
            new Quaternion(data.orientation[0], data.orientation[2], -data.orientation[1], data.orientation[3])
          );
        TargetPose.set(pose);
    }
    catch (error) {
        console.error("Error:", error);
    }
}


export async function setBrightness(newBrightness: number) {
    if (!isConnected) {
        console.error("Not connected to the robot.");
        return;
    }
    fetch(`http://192.168.2.209:1442/setBrightness?newBrightness=${newBrightness}`, {
        method: "POST",
        headers: {
            "accept": "application/json",
        },
    });
}

export let leds = [0, 0, 0, 0, 0, 0, 0]; // Initialize LED states

export async function setLeds() {
    if (!isConnected) {
        console.error("Not connected to the robot.");
        return;
    }

    fetch(`http://192.168.2.209:1442/setLeds`, {
        method: "POST",
        headers: {
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ leds }),
    });
}

export async function setHSL(hue: number, sat: number, light: number) {
    if (!isConnected) {
        console.error("Not connected to the robot.");
        return;
    }
    fetch(`http://192.168.2.209:1442/setHSL?hue=${hue}&sat=${sat}&light=${light}`, {
        method: "POST",
        headers: {
            "accept": "application/json",
        },
    });
}

export let heater = writable(0);

export async function setHeater(newHeat: number) {
    fetch(`http://192.168.2.209:8082/setHeater?setTemp=${newHeat}`, {
        method: "POST",
        headers: {
            "accept": "application/json",
        },
    }).then((response) => {
        return response.json();
    });
}


export async function setTranslationSpeed(arg0: number): Promise<void> {
    //convert mm/s to m/s
    let arg0_m = arg0 / 1000;
    fetch("http://192.168.2.13:8081/api/cartesian", {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            linearVelocity: arg0_m
        }),
    }).then(async (response) => {
        console.log(response);
        //wait 1 second before sending the trigger
        await new Promise(r => setTimeout(r, 1000));
        socket.emit("linearveltrigger", { data: true });
    });
}

export async function setRotationalSpeed(arg0: number): Promise<void> {
    //convert deg/s to rad/s
    let rads = toRad(arg0);
    if (rads > 0.2617994) {
        console.error("Speed too high, setting to max speed.");
        rads = 0.2617994;
    }
    fetch("http://192.168.2.13:8081/api/cartesian", {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            rotationSpeed: rads
        }),
    
    }).then(async (response) => {
        console.log(response);
        //wait 1 second before sending the trigger
        await new Promise(r => setTimeout(r, 1000));
        //42["linearveltrigger",{"data":true}]
        socket.emit("linearveltrigger", { data: true });
    });
}

// curl -X 'POST' \
//   'http://192.168.2.209:1442/setPause?pause=true' \
//   -H 'accept: application/json' \
//   -d ''

export async function setPause(): Promise<void> {
    const pause = !get(isPaused);
    console.log("Pause:", pause);
    
    fetch(`http://192.168.2.209:1442/setPause?pause=${pause}`, {
        method: "POST",
        headers: {
            Accept: "application/json",
        },
    }).then((response) => {
        console.log(response);
    });
}

export async function fetch_cartesian_pose(): Promise<void> {
    try {
        const response = await fetch("http://192.168.2.13:8081/api/cartesianpose");
        const data = await response.json();
        const pose = new Pose(
            new Vector3(data[0].X, data[0].Z, -data[0].Y),
            new Quaternion(data[0]._X, data[0]._Z, -data[0]._Y, data[0]._W)
        );
        robotJoints.update((joints) => {
            joints.x = data[0].X;
            joints.y = data[0].Y;
            joints.z = data[0].Z;
            joints._x = data[0]._X;
            joints._y = data[0]._Y;
            joints._z = data[0]._Z;
            joints._w = data[0]._W;
            return joints;
        });
    } catch (error) {
        console.error("Error:", error);
    }
}

export async function fetch_joints_angle(): Promise<void> {
    try {
        const response = await fetch("http://192.168.2.13:8081/api/jointangles");
        const data = await response.json();
        robotJoints.update((joints) => {
            joints.joint1 = data[0].A1;
            joints.joint2 = data[0].A2;
            joints.joint3 = data[0].A3;
            joints.joint4 = data[0].A4;
            joints.joint5 = data[0].A5;
            joints.joint6 = data[0].A6;
            return joints;
        });
    } catch (error) {
        console.error("Error:", error);
    }
}

export let states = ["normal", "square_detector", "tag_detector"];
export let current_state_index = writable(0);

export async function set_state(state: string): Promise<void> {
    try {
        const response = await fetch(`http://192.168.2.209:1447/set_state/${state}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });
        if (!response.ok) {
            console.error("Failed to set state");
        }
    } catch (error) {
        console.error("Error setting state", error);
    }
}


export async function set_camera(index: number): Promise<void> {
    try {
        const response = await fetch(`http://192.168.2.209:1447/set_camera/${index}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });
        if (!response.ok) {
            console.error("Failed to set camera");
        }
    } catch (error) {
        console.error("Error setting camera", error);
    }
}