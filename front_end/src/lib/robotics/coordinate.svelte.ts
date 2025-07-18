import * as THREE from "three";
import { writable, type Writable, get } from "svelte/store";
import { error, warning } from "$lib/NotificationsLib";

/**
 * Represents a waypoint with a unique name and a position in 3D space.
 */
export class Waypoint {
    constructor(
        public name: string,
        public position: THREE.Vector3
    ) { }
}

/** Stores the current target position. */
export const currentTargetPosition: Writable<THREE.Vector3> = writable(new THREE.Vector3(0, 0.5, 0.25));

/** Stores a future position for potential use. */
export const futurePosition: Writable<THREE.Vector3> = writable(new THREE.Vector3(-0.27, 0.03, 0.36));

/** Stores a future position for potential use. */
export const ApriltagDetection = writable([]);

/** Stores a future position for potential use. */
export const AprilTagRelativePosition: Writable<THREE.Vector3> = writable(new THREE.Vector3(0, 0, 0));
export const AprilTagRotation = writable(new THREE.Quaternion(0, 0, 0, 1));
/** Stores a future position for potential use. */
export const AprilTagPosition: Writable<THREE.Vector3> = writable(new THREE.Vector3(0, 0, 0));


/** Stores a future position for potential use. */
export const AprilTagWorldPosition: Writable<THREE.Vector3> = writable(new THREE.Vector3(0, 0, 0));


export const loadcell_value: Writable<number> = writable(0.0);
export const loadcell_target: Writable<number> = writable(0.0);
export const temperature = writable({});

/** Stores a future position for potential use. */
export const AprilTagInView: Writable<boolean> = writable(false);

/** Stores the current target rotation. */
export const currentTargetRotation: Writable<THREE.Quaternion> = writable(new THREE.Quaternion(0, 0, 0, 1));

/** Stores a future rotation for potential use. */
export const futureRotation: Writable<THREE.Euler> = writable(new THREE.Euler(0, 0, 0, 'YXZ'));

export class Pose {
    constructor(
        public position: THREE.Vector3,
        public rotation: THREE.Quaternion
    ) { }
}

export const trayPoses: Writable<Pose[]> = writable([]);
export const TargetPose: Writable<Pose> = writable(new Pose(new THREE.Vector3(0, 0, 0), new THREE.Quaternion(0, 0, 0, 1)));

/** Stores current robot joints. */
export interface RobotJoints {
    joint1: number;
    joint2: number;
    joint3: number;
    joint4: number;
    joint5: number;
    joint6: number;
    a: any;
    b: any;
    c: any;
    x: any;
    y: any;
    z: any;
    _x: any;
    _y: any;
    _z: any;
    _w: any;
}


export const robotJoints: Writable<RobotJoints> = writable({
    joint1: 0,
    joint2: 0,
    joint3: 0,
    joint4: 0,
    joint5: 0,
    joint6: 0,
    x: 0,
    y: 0,
    z: 0,
    a: 0,
    b: 0,
    c: 0,
    _x: 0,
    _y: 0,
    _z: 0,
    _w: 1,
});

let ws: WebSocket;

export const isPaused: Writable<boolean> = writable(false);
export const torques: Writable<{}> = writable({});
export const autonomous_control: Writable<boolean> = writable(false);
export const threshold: Writable<number> = writable(0.0);
export const unblock_pressure_flag: Writable<boolean> = writable(false);

export let data = writable({});

let daemon_ws: WebSocket;

export const daemonStatusJson = writable({});


export function connect2Demon() {
    daemon_ws = new WebSocket('ws://192.168.2.209:8765/ws');
    console.log("connecting to daemon");
    daemon_ws.onopen = () => {
        console.log('Connected to daemon');
    }
    daemon_ws.onmessage = (event) => {
        daemonStatusJson.set(JSON.parse(event.data));
    }
    daemon_ws.onclose = () => {
        console.log('Disconnected from daemon');
        setTimeout(() => {
            console.log('Reconnecting to daemon...');
            connect2Demon();
        }, 1000);
    };
    daemon_ws.onerror = (error) => {
        console.error('Daemon WebSocket error:', error);
    }
}


export function connectApi() {
    ws = new WebSocket('ws://192.168.2.209:1442/ws');
    console.log("connecting to api");
    
    ws.onopen = () => {
        console.log('Connected to API');
    };
    
    ws.onmessage = (event) => {
        const temp = JSON.parse(event.data);
        if (temp.hasOwnProperty("force")) {
            loadcell_value.set(parseFloat(temp.force));
        }
        if (temp.hasOwnProperty("temperature")) {
            temperature.set(temp.temperature);
        }
        if (temp.hasOwnProperty("is_paused")) {
            isPaused.set(temp.is_paused);
        }
        if (temp.hasOwnProperty("error")) {
            error(JSON.stringify(temp.error), 5000);
        }
        if (temp.hasOwnProperty("warning")) {
            warning(JSON.stringify(temp.warning), 5000);
        }
        if (temp.hasOwnProperty("torques")) {
            torques.set(temp.torques);
        }
        if (temp.hasOwnProperty("autonomous_control")) {
            autonomous_control.set(temp.autonomous_control);
        }
        if (temp.hasOwnProperty("threshold")) {
            threshold.set(temp.threshold);
        }
        if (temp.hasOwnProperty("unblock_pressure_flag")) {
            unblock_pressure_flag.set(temp.unblock_pressure_flag);
        }
        data.set(temp);
    };
    
    ws.onclose = () => {
        console.log('Disconnected from API');
        setTimeout(() => {
            console.log('Reconnecting to API...');
            connectApi();
        }, 1000);
    };
}

let ws_image: WebSocket;
export function connectImage() {
    ws_image = new WebSocket('ws://192.168.2.209:1443/ws');
    ws_image.onopen = () => {
        console.log('Connected to Image');
    };
    ws_image.onmessage = (event) => {

    };
    ws_image.onclose = () => {
        console.log('Disconnected from Image');
    };
}


/** Stores manually added waypoints to avoid duplicates and allow updates. */
export const generalWaypoints: Writable<Waypoint[]> = writable([]);

/** Stores waypoints that are autogenerated based on a configuration. */
export const autoGeneratedWaypoints: Writable<Waypoint[]> = writable([]);

/**
 * Adds a new waypoint or updates an existing one with the same name.
 * @param name - Unique identifier for the waypoint.
 * @param position - Position of the waypoint in 3D space.
 */
export function addOrUpdateWaypoint(name: string, position: THREE.Vector3) {
    generalWaypoints.update((waypoints) => {
        const index = waypoints.findIndex(wp => wp.name === name);
        if (index !== -1) {
            // Update existing waypoint.
            waypoints[index].position.copy(position);
        } else {
            // Add new waypoint.
            waypoints.push(new Waypoint(name, position.clone()));
        }
        return waypoints;
    });
}

export function addWaypointbyName(name: string) {
    generalWaypoints.update((waypoints) => {
        const index = waypoints.findIndex(wp => wp.name === name);
        if (index !== -1) {
            // Update existing waypoint.
            waypoints[index].position.copy(get(currentTargetPosition).clone());
        } else {
            // Add new waypoint.
            waypoints.push(new Waypoint(name, get(currentTargetPosition).clone()));
        }
        return waypoints;
    });
}

/**
 * Clears all manually added waypoints.
 */
export function clearGeneralWaypoints() {
    generalWaypoints.set([]);
}

/**
 * Sets the position of a target object to match the specified waypoint.
 * @param name - Name of the waypoint to use.
 * @param target - The 3D object to position.
 */
export function setWaypoint(name: string, target: THREE.Object3D) {
    const waypoint = getWaypoint(name);
    if (waypoint) {
        target.position.copy(waypoint.position);
    } else {
        console.log("not found")
    }
}

/**
 * Generates waypoints based on a configuration object.
 * @param config - Configuration for grid generation.
 */
export function generateWaypointsFromConfig(config: {
    letters: string,
    rows: number,
    offsetX: number,
    offsetY: number
}) {
    const { letters, rows, offsetX, offsetY } = config;
    const origin = get(robotJoints);
    console.log(origin.x, origin.y, origin.z)
    const newWaypoints: Waypoint[] = [];

    // Generate grid of waypoints.
    for (let row = 0; row < rows; row++) {
        for (let col = 0; col < letters.length; col++) {
            
            const cellName = letters[col] + row;
            const xPos = origin.x + col * offsetX;
            const yPos = origin.y + row * offsetY;
            const zPos = origin.z;
            newWaypoints.push(new Waypoint(cellName, new THREE.Vector3(xPos, yPos, zPos)));
        }
    }

    autoGeneratedWaypoints.set(newWaypoints);
}

export function generateWaypointDefault() {
    const gridConfig = {
        letters: "abcdef", // Columns labeled from 'a' to 'h'.
        rows: 15,             // Number of rows in the grid.
        offsetX: 0.0209999837404,        // Horizontal spacing between waypoints.
        offsetY: 0.0202999871549        // Vertical spacing between waypoints.
    };

    // Generate waypoints using the example configuration.
    generateWaypointsFromConfig(gridConfig);
}

/**
 * Retrieves a waypoint by name from both general and autogenerated waypoints.
 * @param name - Name of the waypoint to retrieve.
 * @returns The waypoint if found, otherwise undefined.
 */
export function getWaypoint(name: string): Waypoint | undefined {
    // Check in general waypoints.
    const general = get(generalWaypoints).find(wp => wp.name === name);
    if (general) return general;

    // Check in autogenerated waypoints.
    const autoGenerated = get(autoGeneratedWaypoints).find(wp => wp.name === name);
    if (autoGenerated) {
        console.log("found")
        console.log(autoGenerated.position)
        return autoGenerated;

    }

    // Waypoint not found.
    return undefined;
}

/**
 * Retrieves all waypoints, both general and autogenerated.
 * @returns An array of all waypoints.
 */
export function getAllWaypoints(): Waypoint[] {
    return [...get(generalWaypoints), ...get(autoGeneratedWaypoints)];
}

/**
 * Clears all autogenerated waypoints.
 */
export function clearAutoGeneratedWaypoints() {
    autoGeneratedWaypoints.set([]);
}


export function readableQuat(quat: THREE.Quaternion) {
    const euler = new THREE.Euler();
    euler.setFromQuaternion(quat);
    return String(
        THREE.MathUtils.radToDeg(euler.x).toFixed(2) +
        " " +
        THREE.MathUtils.radToDeg(euler.y).toFixed(2) +
        " " +
        THREE.MathUtils.radToDeg(euler.z).toFixed(2) +
        " ",
    );
}

export function readableEuler(euler: THREE.Euler) {
    return String(
        THREE.MathUtils.radToDeg(euler.x).toFixed(2) +
        " " +
        THREE.MathUtils.radToDeg(euler.y).toFixed(2) +
        " " +
        THREE.MathUtils.radToDeg(euler.z).toFixed(2) +
        " ",
    );
}

export function readablePosition(Vector3: THREE.Vector3) {
    return String(
        Vector3.x.toFixed(2) +
        " " +
        Vector3.y.toFixed(2) +
        " " +
        Vector3.z.toFixed(2),
    );

}

