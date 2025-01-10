
import socketIOClient from 'socket.io-client';
import { get, writable } from 'svelte/store';
import { toRad } from './utils';
import { isPaused, Pose, robotJoints, trayPoses } from '$lib/coordinate';
import { Vector3, Quaternion } from 'three';
//very important  npm install socket.io-client@2 --save
let isConnected = false;
export const lara_api_joint_stream = writable([0, 0, 0, 0, 0, 0]);

let socket: any;



export function setupSocket() {
    socket = socketIOClient("http://192.168.2.13:8081");

    socket.on("connect", () => {
        console.log(`Connected with socket ID: ${socket.id}`);
        isConnected = true
        setInterval(() => {
            socket.emit("heartbeat_response", true);
        }, 5000);
        console.log("Connected and emitted events.");
    });

    socket.on("heartbeat_check", () => {
        socket.emit("heartbeat_response", true);
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
    // console.log("Sent 'JointGotoManual' stop event.");
}


export async function setTray() {
    try {
        const response = await fetch("http://localhost:1442/setTray", {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        });
        console.log("Set tray response:", response);
        const data = await response.json();
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
        const response = await fetch("http://localhost:1442/getTray", {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        });
        console.log("Get tray response:", response);
        const data = await response.json();
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


export const max_translation_speed = 0.25; // 250mm/s

export async function setTranslationSpeed(arg0: number): Promise<void> {
    //max 250mm/s
    if (arg0 > max_translation_speed) {
        console.error("Speed too high, setting to max speed.");
        arg0 = max_translation_speed;
    }
    fetch("http://192.168.2.13:8081/api/cartesian", {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            linearVelocity: arg0
        }),
    }).then((response) => {
        console.log(response);
        socket.emit("linearveltrigger", { data: true });
    });
}

export const max_rotation_speed = 0.2617994 // radians/s

export async function setRotationalSpeed(arg0: number): Promise<void> {
    //max 250mm/s
    if (arg0 > max_rotation_speed) {
        console.error("Speed too high, setting to max speed.");
        arg0 = max_rotation_speed;
    }
    fetch("http://192.168.2.13:8081/api/cartesian", {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            rotationSpeed: arg0
        }),
    }).then((response) => {
        console.log(response);
        //42["linearveltrigger",{"data":true}]
        socket.emit("rotationalveltrigger", { data: true });
    });
}

// curl -X 'POST' \
//   'http://localhost:1442/setPause?pause=true' \
//   -H 'accept: application/json' \
//   -d ''

export async function setPause(): Promise<void> {
    const pause = !get(isPaused);
    console.log("Pause:", pause);
    
    fetch(`http://localhost:1442/setPause?pause=${pause}`, {
        method: "POST",
        headers: {
            Accept: "application/json",
        },
    }).then((response) => {
        console.log(response);
    });
}