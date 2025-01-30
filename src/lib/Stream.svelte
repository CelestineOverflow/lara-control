<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import * as THREE from "three";
    import { OrbitControls } from "three/addons/controls/OrbitControls.js";
    import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
    import { RectAreaLightHelper } from "three/examples/jsm/helpers/RectAreaLightHelper.js";
    import ThreeMeshUI from "three-mesh-ui";
    import RobotData from "./RobotData.svelte";
    import {
        Pose,
        robotJoints,
        TargetPose,
        trayPoses,
    } from "$lib/coordinate";
    import { Lara } from "./robotics/lara";
    import { Pane, Splitpanes } from "svelte-splitpanes";
    import ObjectControl from "$lib/ObjectControl";
    //Enviroment Variable
    let canvas: HTMLCanvasElement;
    let scene: THREE.Scene;
    let camera: any;
    let renderer: THREE.WebGLRenderer;
    let animationId: number;
    let controls: OrbitControls;
    let resizeObserver: ResizeObserver;
    let container: HTMLDivElement;
    let controlsObject: ObjectControl;
    //Robot Varibles
    let laraArm: Lara;
    let clock: THREE.Clock;
    // Enviroment visual
    let GeneralSceneGLB: THREE.Group | null = null;
    let arrowHelper: THREE.ArrowHelper | null = null;
   
    let canvas_overlay_rendered: THREE.WebGLRenderer;
    let canvas_overlay: HTMLCanvasElement;
    let camerahtml: any;
    let tCube: THREE.Mesh;

    let customFOV = 75;


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
    const cubemat = new THREE.MeshBasicMaterial({ color: 0xff0000 , wireframe: true});

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


    let targetMarker: THREE.Mesh | null = null;
    function addSingleTargetMarker(pose: Pose) {
        //check if scene is loaded
        if (!scene) return;
        if (targetMarker) scene.remove(targetMarker);
        const mesh = new THREE.Mesh(cubegeo, cubemat);
        mesh.setRotationFromQuaternion(pose.rotation);
        mesh.position.copy(pose.position);
        scene.add(mesh);
        targetMarker = mesh;
    }
    let boxWidth = 1.0;
    let boxHeight = 1.0;
    let boxDepth = 1.0;

    function addBox() {
        objectControl?.addBox(boxWidth, boxHeight, boxDepth);
    }
    function setTransformMode(mode) {
        objectControl?.setTransformMode(mode);
    }

 

    function setupOverlayRender() {
        // Set fixed width and height to 720p (1280x720)
        canvas_overlay_rendered = new THREE.WebGLRenderer({
            canvas: canvas_overlay,
        });

        canvas_overlay_rendered.setClearColor(0x000000, 0);
        canvas_overlay_rendered.autoClear = false;
        canvas_overlay_rendered.setSize(1280, 720);
        arrowHelper = new THREE.ArrowHelper(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(0, 0, 0),
            0.5,
            0xff0000,
            0.1,
            0.05,
        );
        scene.add(arrowHelper);
    }


    function overlayResizeHandler() {
        //keer the render aspect ratio to 16:9

    // if (!camerahtml) return;
    // const rect = camerahtml.getBoundingClientRect();
    // const width = rect.width;
    // const height = rect.height;
    // camera.aspect = 1280 / 720;
    // camera.updateProjectionMatrix();
    // canvas_overlay_rendered.setSize(width, height);

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

        setupOverlayRender();
        renderer.setSize(width, height);
        // Initialize controls
        controls = new OrbitControls(camera, renderer.domElement);
        controls.update();
        // Setup object control
        controlsObject = new ObjectControl({
            scene,
            camera,
            renderer,
            controls,
            domElement: renderer.domElement,
        });

        // Add lights
        addLights();
        // add gtlf model
        // let gtlfloader = new GLTFLoader();
        // gtlfloader.load("gtlf/GeneralScene.glb", (gltf) => {
        //     GeneralSceneGLB = gltf.scene;

        //     scene.add(GeneralSceneGLB);
        // });
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
            // overlayResizeHandler();
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
            // Clear the offscreen renderer before rendering
            canvas_overlay_rendered.clear();
            if (laraArm.camera) {
                if (arrowHelper) {
                    arrowHelper.visible = false;
                }
                if (tCube) {
                    tCube.visible = false;
                }
                canvas_overlay_rendered.render(scene, laraArm.camera);
                //hide general scene
                if (GeneralSceneGLB) {
                    GeneralSceneGLB.visible = false;
                }
                //set camera asperct ratio
                if (laraArm.camera) {
                    //set fov
                    laraArm.camera.fov = customFOV;
                    const rect = camerahtml.getBoundingClientRect();
                    const width = rect.width;
                    const height = rect.height;
                    laraArm.camera.aspect = width / height;
                    laraArm.camera.updateProjectionMatrix();
                    canvas_overlay_rendered.setSize(width, height);
                }
                canvas_overlay_rendered.render(scene, laraArm.camera);
                if (arrowHelper) {
                    arrowHelper.visible = true;
                }
                if (tCube) {
                    tCube.visible = true;
                }
                if (GeneralSceneGLB) {
                    GeneralSceneGLB.visible = true;
                }
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
    TargetPose.subscribe((pose) => {
        addSingleTargetMarker(pose);
    });
    // http://localhost:1692/my_camera
</script>

<div class="overlay">
    <label>
        Box Width
        <input type="number" bind:value={boxWidth} step="0.1" />
    </label>
    <label>
        Box Height
        <input type="number" bind:value={boxHeight} step="0.1" />
    </label>
    <label>
        Box Depth
        <input type="number" bind:value={boxDepth} step="0.1" />
    </label>
    <button on:click={addBox}>Add Box</button>
    <hr />
    <button on:click={() => setTransformMode("translate")}>Move</button>
    <button on:click={() => setTransformMode("rotate")}>Rotate</button>
    <button on:click={() => setTransformMode("scale")}>Scale</button>
    <input type="number" bind:value={customFOV} step="1" />
</div>


<Splitpanes horizontal={true}>
    <Pane snapSize={10}>
        <!-- Your main canvas pane -->

        <div
            bind:this={container}
            style="width: 100%; height: 800px; position: relative;"
        >
            <canvas bind:this={canvas} style="display: block;"></canvas>
            <div
                style="position: absolute; top: 10px; right: 10px; color: white; z-index: 1;"
            >
                <RobotData />
            </div>
        </div>
    </Pane>
    <Pane>
        <div style="width: 100%; height: 100%; position: relative;">
            <!-- The camera feed -->
            <img
            width="1280"
            height="720"
            bind:this={camerahtml}
            src="http://localhost:1692/my_camera"
            alt="Camera feed"
            style="width: 1280px; height: 720px; position: absolute; top: 0; left: 0;"
            on:load={overlayResizeHandler}
            />
            <!-- The overlay canvas -->
            <canvas
            width="1280"
            height="720"
            bind:this={canvas_overlay}
            style="position: absolute; top: 0; left: 0; background: transparent; width: 1280px; height: 720px;"
            ></canvas>
        </div>
    </Pane>
</Splitpanes>

<style>
    .overlay {
        position: absolute;
        top: 5em;
        left: 1rem;
        background: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        border-radius: 4px;
        z-index: 10;
    }
    .overlay label,
    .overlay input {
        display: block;
    }
    .overlay button {
        margin-top: 0.5rem;
        margin-right: 0.5rem;
    }
</style>
