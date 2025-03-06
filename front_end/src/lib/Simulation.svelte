<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
    import { TransformControls } from "three/examples/jsm/controls/TransformControls.js";
    import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
    import {futurePosition,futureRotation,type RobotJoints,} from "$lib/coordinate";
    import ControlPad from "./ControlPad.svelte";
    import RobotData from "./RobotData.svelte";
    import Apriltag from "./Apriltag.svelte";
    import * as THREE from "three/webgpu";
    import { toRad } from "$lib/robotics/utils";
    import { Lara } from "./robotics/lara";
    import Webrtc from "./Webrtc.svelte";
    import { lara_api_joint_stream, setupSocket, startMovement } from "./robotics/laraapi";

    //Enviroment Variable
    let canvas: HTMLCanvasElement;
    let scene: THREE.Scene;
    let camera1: any;
    let camera2: any;
    let renderer: THREE.WebGPURenderer;
    let offscreenRenderer: THREE.WebGPURenderer;
    let animationId: number;
    let controls: OrbitControls;
    let resizeObserver: ResizeObserver;
    let container: HTMLDivElement;
    let SCREEN_WIDTH: number = 0;
    let SCREEN_HEIGHT: number = 0;
    // OpenCV
    let openCVModuleStarted = false;
    //Robot Varibles
    let laraArm: Lara;
    let transformControls: TransformControls;
    let transformControls2: TransformControls;
    //debugging variables
    let targetPivot: THREE.Mesh;
    let cube: THREE.Mesh;
    let cube1: THREE.Mesh;
    let cube22: THREE.Mesh;
    let stream: any;
    // let stats: Stats;
    let controlMesh: any;

    function CanvasSizeHandler() {
            SCREEN_WIDTH = container.clientWidth;
            SCREEN_HEIGHT = container.clientHeight;
            camera1.aspect = SCREEN_WIDTH / SCREEN_HEIGHT;
            camera1.updateProjectionMatrix();
            renderer.setSize(SCREEN_WIDTH, SCREEN_HEIGHT);
            // offscreenRenderer.setSize(SCREEN_WIDTH, SCREEN_HEIGHT);
        }
        
    let last_time = 0;
    let timeInterval = 100; //miliseconds

    function animate() {
            
            CanvasSizeHandler();
            animationId = requestAnimationFrame(animate);
            //Offscreen Render
            transformControls.getHelper().visible = false;
            transformControls2.getHelper().visible = false;
            offscreenRenderer.clear(); // Clear the offscreen renderer before rendering
            offscreenRenderer.render(scene, camera2);
            //On Screen Render
            transformControls.getHelper().visible = true;
            transformControls2.getHelper().visible = true;
            targetSymbol.visible = true;
            renderer.clear();
            renderer.render(scene, camera1);
            targetSymbol.visible = false;
            // Update controls
            controls.update();

            if (controlMesh && cube22) {

                controlMesh.position.copy(cube22.position);
            }
            // Update the joints based on the bones' rotations
            if (laraArm.loaded) {
                try {
                    laraArm.update();
                    const { Quat: EndActuatorQuat, Pos: EndActuatorPos } = laraArm.getLinkMatrix("lara10_flange");
                    camera2.position.copy(EndActuatorPos);
                    const cameraOffset = new THREE.Quaternion();
                    cameraOffset.copy(EndActuatorQuat);
                    cameraOffset.multiplyQuaternions(
                        cameraOffset,
                        new THREE.Quaternion().setFromEuler(
                            new THREE.Euler(toRad(-180), 0, toRad(180)),
                        ),
                    );
                    camera2.rotation.setFromQuaternion(cameraOffset);
                    // Offset to be zero
                    EndActuatorQuat.multiply(
                        new THREE.Quaternion().setFromEuler(
                            new THREE.Euler(toRad(-90), 0, 0),
                        ),
                    );
                    let EndActuatorEuler = new THREE.Euler();
                    EndActuatorEuler.setFromQuaternion(EndActuatorQuat);
                    //User Input
                    let target = $futureRotation.clone();
                    let targetQuat = new THREE.Quaternion().setFromEuler(
                        target,
                    );
                    let targetEuler = new THREE.Euler();
                    targetEuler.setFromQuaternion(targetQuat);
                    let diffQuat = targetQuat
                        .clone()
                        .multiply(EndActuatorQuat.clone().invert());
                    let diffEuler = new THREE.Euler();
                    diffEuler.setFromQuaternion(diffQuat, "YXZ");
                    cube.position.copy(EndActuatorPos);
                    cube.visible = false;
                    cube1.visible = false;
                    let { Quat: linkQuat, Pos: linkPos } =
                        laraArm.getLinkMatrix("lara10_link5");
                    let diffVector = new THREE.Vector3();
                    diffVector.x = cube.position.x - linkPos.x;
                    diffVector.y = cube.position.y - linkPos.y;
                    diffVector.z = cube.position.z - linkPos.z;
                    laraArm.targetBone.position.x =
                        targetPivot.position.x - diffVector.x;
                    laraArm.targetBone.position.y =
                        targetPivot.position.y - diffVector.y;
                    laraArm.targetBone.position.z =
                        targetPivot.position.z - diffVector.z;

                    lara_api_joint_stream.set([
                        laraArm.joint1.value,
                        laraArm.joint2.value,
                        laraArm.joint3.value,
                        laraArm.joint4.value,
                        laraArm.joint5.value,
                        laraArm.joint6.value,
                    ])
                    startMovement();
                    
                    laraArm.joint4.add(diffEuler.z);
                    laraArm.joint5.add(diffEuler.x);
                    laraArm.joint6.add(-diffEuler.y);
                } catch (error) {
                    console.error(error);
                }
            }
        }


    function addLights() {
        const light0 = new THREE.PointLight(0xff0000, 4, 100);
        light0.position.set(0, 1, 0);
        scene.add(light0);
        const light1 = new THREE.PointLight(0x00ff00, 4, 100);
        light1.position.set(2, 1, 0);
        scene.add(light1);
        const light2 = new THREE.PointLight(0x0000ff, 4, 100);
        light2.position.set(0, 1, 2);
        scene.add(light2);
        scene.add(new THREE.AmbientLight(0x404040, 5));
    }

    let offscreenCanvas: HTMLCanvasElement;

    let targetSymbol: THREE.Mesh;

    function addTarget() {
        const geometry = new THREE.CylinderGeometry(0.01, 0.01, 0.1, 8);
        const material = new THREE.MeshBasicMaterial({ color: 0xffff00 });
        targetSymbol = new THREE.Mesh(geometry, material);
        scene.add(targetSymbol);
    }
    onMount(async () => {
        setupSocket();
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;

        offscreenCanvas = document.createElement("canvas");
        offscreenCanvas.width = 1000;
        offscreenCanvas.height = 1000;
        stream = offscreenCanvas.captureStream();
        // offscreen rendered setup
        offscreenRenderer = new THREE.WebGPURenderer({
            canvas: offscreenCanvas,
        });
        offscreenRenderer.autoClear = false;
        offscreenRenderer.setSize(1000,1000);

        // Initialize scene
        scene = new THREE.Scene();
        // Initialize camera 1

        camera1 = new THREE.PerspectiveCamera(75, width / height, 0.01, 100);
        camera1.position.z = 1;
        camera1.position.y = 1;
        camera1.position.x = 1;
        // Initialize camera 2
        camera2 = new THREE.PerspectiveCamera(75, 1000 / 1000, 0.01, 1000);
        camera2.position.z = 1;
        camera2.position.y = 1;
        camera2.position.x = 1;
        scene.add(camera2);
        SCREEN_WIDTH = window.innerWidth;
        SCREEN_HEIGHT = window.innerHeight;
        // Initialize renderer
        renderer = new THREE.WebGPURenderer({ canvas });
        renderer.autoClear = false;
        renderer.setSize(width, height);

        // Initialize controls
        controls = new OrbitControls(camera1, renderer.domElement);
        controls.update();

        // Add lights
        addLights();
        addTarget();
        transformControls = new TransformControls(camera1, renderer.domElement);
        transformControls.size = 0.75;
        transformControls.space = "world";
        transformControls2 = new TransformControls(
            camera1,
            renderer.domElement,
        );
        transformControls2.size = 0.75;
        transformControls2.space = "world";

        scene.add(transformControls.getHelper());
        scene.add(transformControls2.getHelper());

        // disable orbitControls while using transformControls
        transformControls.addEventListener("change", ()=>{
            handleTransformChange()
        });
        transformControls.addEventListener("mouseDown", () => {
            controls.enabled = false;
            isInteracting = true;
        });
        transformControls.addEventListener("mouseUp", () => {
            controls.enabled = true;
            isInteracting = false;
        });
        transformControls2.addEventListener("mouseDown", () => {
            controls.enabled = false;
            isInteracting = true;
        });
        transformControls2.addEventListener("change", ()=>{
            handleTransformChange()
        });
        transformControls2.addEventListener("mouseUp", () => {
            controls.enabled = true;
            isInteracting = false;
        });
        // add gtlf model
        let gtlfloader = new GLTFLoader();
        gtlfloader.load(
            "gtlf/GeneralSceneLara.glb",
            (gltf) => {
                const model = gltf.scene;
                model.scale.set(0.2, 0.2, 0.2); // Scale down by 1000
                model.rotation.y = -Math.PI / 2;
                scene.add(model);
                console.log("Model loaded successfully");
            },
            (xhr) => {
                console.log((xhr.loaded / xhr.total) * 100 + "% loaded");
            },
            (error) => {
                console.error("An error happened", error);
            },
        );

        // Add control mesh
        gtlfloader.load(
            "gtlf/board.glb",
            (gltf) => {
                controlMesh = gltf.scene;
                controlMesh.position.z +=.01;
                controlMesh.scale.set(0.2, 0.2, 0.2); // Scale down by 1000
                controlMesh.rotation.y = -Math.PI / 2;
                scene.add(controlMesh);
                console.log("Control mesh loaded successfully");
            },
            (xhr) => {
                console.log((xhr.loaded / xhr.total) * 100 + "% loaded");
            },
            (error) => {
                console.error("An error happened", error);
            },
        );

        const cubeGeometry11 = new THREE.BoxGeometry(0.01, 0.01, 0.01);
        const cubeMaterial22 = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
         cube22 = new THREE.Mesh(cubeGeometry11, cubeMaterial22);
        scene.add(cube22);

        // Test Cube
        const cubeGeometry = new THREE.BoxGeometry(0.1, 0.1, 0.1);
        const cubeMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
        cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
        cube1 = new THREE.Mesh(cubeGeometry, cubeMaterial);
        targetPivot = new THREE.Mesh();
        targetPivot.position.set(0, 0.5, 0.25);
        cube.position.set(0, 0, 0);
        scene.add(cube);
        scene.add(cube1);
        scene.add(targetPivot);

        transformControls2.attach(cube22);
        transformControls.attach(targetPivot);
        //Lara Arm
        laraArm = new Lara(scene);
        animate();
    });

    onDestroy(() => {
        if (animationId) cancelAnimationFrame(animationId);
        if (resizeObserver) resizeObserver.disconnect();

        controls.dispose();
        renderer.dispose();
    });

    let isInteracting  = false;

    function handleTransformChange() {
    if (targetPivot) {
        isInteracting = true;
        // console.log("handletransform")
        futurePosition.set(targetPivot.position.clone());
        isInteracting = false;
    }
}


    futurePosition.subscribe((value) => {
        if (!isInteracting && targetPivot) {
            targetPivot.position.copy(value);
        }
    });

   
</script>

<div
    bind:this={container}
    style="width: 100%; height: 800px; position: relative;"
>
    <canvas bind:this={canvas} style="display: block;"></canvas>
    <div
        style="position: absolute; top: 10px; left: 10px; color: white; z-index: 1;"
    >
        <ControlPad />
        <RobotData />
        <button on:click={()=>{laraArm.moveRealRobot()}}>Move Real Robot</button>
    </div>
</div>

<button on:click={()=>{openCVModuleStarted=true}}>opencv</button>
{#if openCVModuleStarted}
<Apriltag {stream} />
<Webrtc {stream} />
{/if}

