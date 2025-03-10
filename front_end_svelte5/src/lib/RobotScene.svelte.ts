// File: RobotScene.ts - Shared scene and state management

import * as THREE from "three";
import { writable } from "svelte/store";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RectAreaLightHelper } from "three/examples/jsm/helpers/RectAreaLightHelper.js";
import { Lara } from "./robotics/lara";
import { robotJoints, TargetPose, trayPoses, type Pose } from "$lib/robotics/coordinate";

// Shared scene and resources
class RobotScene {
  scene: THREE.Scene;
  laraArm: Lara | null = null;
  clock: THREE.Clock;
  GeneralSceneGLB: THREE.Group | null = null;
  arrowHelper: THREE.ArrowHelper | null = null;
  targetMarker: THREE.Mesh | null = null;
  cubes: THREE.Mesh[] = [];
  isInitialized: boolean = false;
  
  // Geometry and materials for markers
  private cubegeo = new THREE.BoxGeometry(0.01, 0.01, 0.01);
  private cubemat = new THREE.MeshBasicMaterial({ color: 0xff0000, wireframe: true });

  constructor() {
    this.scene = new THREE.Scene();
    this.clock = new THREE.Clock();
    this.setupScene();
    
    // We'll initialize the robot arm later in a browser-only context
    
    // Subscribe to pose changes (only if in browser)
    if (typeof window !== 'undefined') {
      trayPoses.subscribe((poses) => {
        this.addTrayMarkers(poses);
      });

      TargetPose.subscribe((pose) => {
        this.addSingleTargetMarker(pose);
      });
    }
  }
  
  // Initialize robot arm - call this only in browser context
  initRobotArm() {
    if (!this.isInitialized && typeof window !== 'undefined') {
      this.laraArm = new Lara(this.scene);
      this.isInitialized = true;
    }
    return this;
  }

  private setupScene() {
    this.addLights();
    
    // Initialize Arrow Helper
    this.arrowHelper = new THREE.ArrowHelper(
      new THREE.Vector3(0, 0, 1),
      new THREE.Vector3(0, 0, 0),
      0.5,
      0xff0000,
      0.1,
      0.05
    );
    this.scene.add(this.arrowHelper);
    
    // Load GLTF model if needed
    // let gtlfloader = new GLTFLoader();
    // gtlfloader.load("gtlf/GeneralScene.glb", (gltf) => {
    //   this.GeneralSceneGLB = gltf.scene;
    //   this.scene.add(this.GeneralSceneGLB);
    // });
  }

  private addLights() {
    const light0 = new THREE.PointLight(0xff0000, 4, 100);
    light0.position.set(0, 1, 0);
    this.scene.add(light0);
    
    const light1 = new THREE.PointLight(0x00ff00, 4, 100);
    light1.position.set(2, 1, 0);
    this.scene.add(light1);
    
    const light2 = new THREE.PointLight(0x0000ff, 4, 100);
    light2.position.set(0, 1, 2);
    this.scene.add(light2);
    
    this.scene.add(new THREE.AmbientLight(0x404040, 5));
    
    const rectLight1 = new THREE.RectAreaLight(0xff0000, 5, 4, 10);
    rectLight1.position.set(-5, 5, 5);
    this.scene.add(rectLight1);
    
    const rectLight2 = new THREE.RectAreaLight(0x00ff00, 5, 4, 10);
    rectLight2.position.set(0, 5, 5);
    this.scene.add(rectLight2);
    
    const rectLight3 = new THREE.RectAreaLight(0x0000ff, 5, 4, 10);
    rectLight3.position.set(5, 5, 5);
    this.scene.add(rectLight3);
    
    this.scene.add(new RectAreaLightHelper(rectLight1));
    this.scene.add(new RectAreaLightHelper(rectLight2));
    this.scene.add(new RectAreaLightHelper(rectLight3));
  }

  addTrayMarkers(poses: Pose[]) {
    // Remove existing cubes
    this.cubes.forEach((cube) => this.scene.remove(cube));
    this.cubes = [];
    
    // Add new cubes
    poses.forEach((pose) => {
      const mesh = new THREE.Mesh(this.cubegeo, this.cubemat);
      mesh.setRotationFromQuaternion(pose.rotation);
      mesh.position.copy(pose.position);
      this.scene.add(mesh);
      this.cubes.push(mesh);
    });
  }

  addSingleTargetMarker(pose: Pose) {
    if (this.targetMarker) this.scene.remove(this.targetMarker);
    
    const mesh = new THREE.Mesh(this.cubegeo, this.cubemat);
    mesh.setRotationFromQuaternion(pose.rotation);
    mesh.position.copy(pose.position);
    this.scene.add(mesh);
    this.targetMarker = mesh;
  }

  updateJoints() {
    if (this.laraArm.loaded) {
      // this.laraArm.joint1.set(robotJoints.get().joint1);
      // this.laraArm.joint2.set(robotJoints.get().joint2);
      // this.laraArm.joint3.set(robotJoints.get().joint3);
      // this.laraArm.joint4.set(robotJoints.get().joint4);
      // this.laraArm.joint5.set(robotJoints.get().joint5);
      // this.laraArm.joint6.set(robotJoints.get().joint6);
    }
  }
}

// Create a singleton instance to be shared across components
export const robotScene = new RobotScene();

// Expose a store for the custom FOV
export const customFOV = writable(75);