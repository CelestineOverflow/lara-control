<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import * as THREE from "three";
    import { OrbitControls } from "three/addons/controls/OrbitControls.js";
    import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
    import { RectAreaLightHelper } from "three/examples/jsm/helpers/RectAreaLightHelper.js";
    import ThreeMeshUI from "three-mesh-ui";
    import RobotData from "./RobotData.svelte";
    import {ApriltagDetection, AprilTagRelativePosition, AprilTagRotation, Pose, robotJoints, trayPoses} from "$lib/coordinate";
    import { Lara } from "./robotics/lara";
    import Apriltag from "./Apriltag.svelte";
    import { Pane, Splitpanes } from 'svelte-splitpanes';
    //Enviroment Variable
    let canvas: HTMLCanvasElement;
    let cv_canvas: HTMLCanvasElement;
    let scene: THREE.Scene;
    let camera: any;
    let renderer: THREE.WebGLRenderer;
    let animationId: number;
    let controls: OrbitControls;
    let resizeObserver: ResizeObserver;
    let container: HTMLDivElement;
    //Robot Varibles
    let laraArm : Lara;
    let clock : THREE.Clock;
    let stream: MediaStream | null = null;
    let enabled = false;
    
    let GeneralSceneGLB: THREE.Group | null = null;
    let arrowHelper: THREE.ArrowHelper | null = null;
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
        const rectLight1 = new THREE.RectAreaLight(0xff0000, 5, 4, 10);
        rectLight1.position.set(-5, 5, 5);
        scene.add(rectLight1);
        const rectLight2 = new THREE.RectAreaLight(0x00ff00, 5, 4, 10);
        rectLight2.position.set(0, 5, 5);
        scene.add(rectLight2);
        const rectLight3 = new THREE.RectAreaLight(0x0000ff, 5, 4, 10);
        rectLight3.position.set(5, 5, 5);
        scene.add(rectLight3);
        scene.add(new RectAreaLightHelper(rectLight1));
        scene.add(new RectAreaLightHelper(rectLight2));
        scene.add(new RectAreaLightHelper(rectLight3));
        
    }


    const cubegeo = new THREE.BoxGeometry(0.01, 0.01, 0.01);
    const cubemat = new THREE.MeshBasicMaterial({ color: 0xff0000 });


    let cubes = [];
    function addTrayMarkers(poses: Pose[]) {
        // Remove existing cubes
        cubes.forEach((cube) => scene.remove(cube));
        cubes = [];
        // Add new cubes
        poses.forEach((pose) => {
        const mesh = new THREE.Mesh(cubegeo, cubemat);
        mesh.setRotationFromQuaternion(pose.rotation);
        mesh.position.copy(pose.position);
        scene.add(mesh);
        cubes.push(mesh);
        });
    }

    let offscreenRenderer: THREE.WebGLRenderer;
    let overlayRenderer: THREE.WebGLRenderer;
    let cv_overlay: HTMLCanvasElement;
    let tCube: THREE.Mesh;

    function setupOffscreen(){
        cv_canvas.width = 1000;
        cv_canvas.height = 1000;
        stream = cv_canvas.captureStream();
        // offscreen rendered setup
        offscreenRenderer = new THREE.WebGLRenderer({
            canvas: cv_canvas,
        });
        offscreenRenderer.autoClear = false;
        offscreenRenderer.setSize(1000,1000);
        //make a pseudo canvas on top of the offscreen canvas
        cv_overlay.width = 1000;
        cv_overlay.height = 1000;
        overlayRenderer = new THREE.WebGLRenderer({
            canvas: cv_overlay,
        });
        overlayRenderer.autoClear = false;
        overlayRenderer.setSize(1000,1000);
        // Add the overlay items
        tCube = new THREE.Mesh(
            new THREE.BoxGeometry(0.075, 0.075, 0.075),
            new THREE.MeshBasicMaterial({ color: 0xff0000 , wireframe: true})
        );
        tCube.position.set(1, 1, 1);
        scene.add(tCube);
        arrowHelper = new THREE.ArrowHelper(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(0, 0, 0),
            0.5,
            0xff0000,
            0.1,
            0.05
        );
        scene.add(arrowHelper);



    }

    onMount(() => {
        //init clock
        clock = new THREE.Clock();
        // Initialize scene
        scene = new THREE.Scene();
        // Initialize camera
        const width = 1000;
        const height = 1000;
        camera = new THREE.PerspectiveCamera(75, width / height, 0.01, 1000);
        // camera = new THREE.OrthographicCamera( width / - 2, width / 2, height / 2, height / - 2, 1, 1000 );
        camera.position.z = 1;
        camera.position.y = 1;
        camera.position.x = 1;
        // Initialize renderer
        renderer = new THREE.WebGLRenderer({ canvas });

        setupOffscreen();
        renderer.setSize(width, height);
        // Initialize controls
        controls = new OrbitControls(camera, renderer.domElement);
        controls.update();
        // Add lights
        addLights();
        // add gtlf model
        let gtlfloader = new GLTFLoader();
        gtlfloader.load("gtlf/GeneralScene.glb", (gltf) => {
            GeneralSceneGLB = gltf.scene;
            scene.add(GeneralSceneGLB);
        });
        // Load the robot
        laraArm = new Lara(scene);
        // Handle canvas resize
        function CanvasSizeHandler() {
            const width = container.clientWidth;
            const height = container.clientHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }

        function animate() {
            ThreeMeshUI.update();
            CanvasSizeHandler();
            animationId = requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);

            // Update the joints based on the bones' rotations
            if (laraArm.loaded) {
                laraArm.joint1.set($robotJoints.joint1);
                laraArm.joint2.set($robotJoints.joint2);
                laraArm.joint3.set($robotJoints.joint3);
                laraArm.joint4.set($robotJoints.joint4);
                laraArm.joint5.set($robotJoints.joint5);
                laraArm.joint6.set($robotJoints.joint6);
            }
            offscreenRenderer.clear(); // Clear the offscreen renderer before rendering
            if (laraArm.camera) {
                if (arrowHelper) {
                    arrowHelper.visible = false;
                }
                if (tCube) {
                    tCube.visible = false;
                }
                offscreenRenderer.render(scene, laraArm.camera);
                //hide general scene
                if (GeneralSceneGLB) {
                    GeneralSceneGLB.visible = false;
                }
                overlayRenderer.render(scene, laraArm.camera);
                if (arrowHelper) {
                    arrowHelper.visible = true;
                }
                if (tCube) {
                    tCube.visible = true;
                }
                if (GeneralSceneGLB) {
                    GeneralSceneGLB.visible = true;
                }
                Overlay();
            }
        }

        animate();
    });

    onDestroy(() => {
        if (animationId) cancelAnimationFrame(animationId);
        if (resizeObserver) resizeObserver.disconnect();

        controls.dispose();
        renderer.dispose();
    });


    trayPoses.subscribe((poses) => {
        addTrayMarkers(poses);
    });

    function Overlay() {
        if ($ApriltagDetection && $ApriltagDetection.length > 0) {
            $ApriltagDetection.forEach((det) => {
                if (tCube) {
                    // Get the rotation vector (q) and translation vector (p) from solvePnP
                    let factor = 0.43; 
                    let p = $AprilTagRelativePosition; // Translation vector from solvePnP
                    let quaternion = $AprilTagRotation;   // Quat 
                    // Adjust the translation vector to match Three.js coordinate system
                    p = new THREE.Vector3(p.z, p.y, p.x);
                    p.multiplyScalar(factor);
                    console.log(`Apriltag pos: ${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)}`);
                    // Get camera position and rotation in world coordinates
                    let cameraPosition = new THREE.Vector3();
                    let cameraRotation = new THREE.Quaternion();
                    laraArm.camera?.getWorldPosition(cameraPosition);
                    laraArm.camera?.getWorldQuaternion(cameraRotation);
                    // Use the forward direction the camera is looking at
                    let eulerCamera = new THREE.Euler();
                    //use the direction the camera is looking at
                    tCube.position.set(cameraPosition.x, cameraPosition.y - .3, cameraPosition.z);
                    eulerCamera.setFromQuaternion(cameraRotation);
                    // console.log(`Camera rot: ${eulerCamera.x.toFixed(2)}, ${eulerCamera.y.toFixed(2)}, ${eulerCamera.z.toFixed(2)}`);
                    let adjustedCameraRotation = cameraRotation.clone().multiply(new THREE.Quaternion(-0.5, 0.5, 0.5, -0.5));
                    eulerCamera.setFromQuaternion(adjustedCameraRotation);
                    // console.log(`d Camera rot: ${eulerCamera.x.toFixed(2)}, ${eulerCamera.y.toFixed(2)}, ${eulerCamera.z.toFixed(2)}`);
                    let eulerApriltag = new THREE.Euler();
                    eulerApriltag.setFromQuaternion(quaternion);
                    // console.log(`Apriltag rot: ${eulerApriltag.x.toFixed(2)}, ${eulerApriltag.y.toFixed(2)}, ${eulerApriltag.z.toFixed(2)}`);
                    quaternion = quaternion.clone().multiply(adjustedCameraRotation);
                    tCube.rotation.setFromQuaternion(quaternion);
                    console.log(`Camera Pos: ${cameraPosition.x.toFixed(2)}, ${cameraPosition.y.toFixed(2)}, ${cameraPosition.z.toFixed(2)}`);
                    tCube.position.set(cameraPosition.x + p.x, cameraPosition.y - p.y, cameraPosition.z - p.z);
                    console.log(`Cube pos: ${tCube.position.x.toFixed(2)}, ${tCube.position.y.toFixed(2)}, ${tCube.position.z.toFixed(2)}`);
                    arrowHelper?.setDirection(new THREE.Vector3(0, -1, 0).applyQuaternion(quaternion));
                    arrowHelper?.position.copy(cameraPosition);
                }
            });
        }
    }
    // http://localhost:1692/my_camera
</script>


<button on:click={() => enabled = !enabled}>{enabled ? "Disable" : "Enable"}</button>
{#if enabled}
    <Apriltag {stream}  />
{/if}

<Splitpanes  horizontal={true}>
<Pane snapSize={10}>
<!-- Your main canvas pane -->
<div bind:this={container} style="width: 100%; height: 800px; position: relative;">
<canvas bind:this={canvas} style="display: block;"></canvas>
<div style="position: absolute; top: 10px; right: 10px; color: white; z-index: 1;">
<RobotData/>
</div>
</div>
</Pane>
<Pane>
<!-- Wrap canvases in a relative container -->
<div style="width: 100%; height: 100%; position: relative; display: none;">
<canvas
        bind:this={cv_canvas}
        style="position: absolute; top: 0; left: 0; width: 30%; height: 30%;"
></canvas>
<canvas
        bind:this={cv_overlay}
        style="position: absolute; top: 0; left: 0; width: 30%; height: 30%;"
></canvas>
</div>
<img src="http://localhost:1692/my_camera" alt="Camera feed" />

</Pane>
</Splitpanes>