<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import * as THREE from "three";
    import { OrbitControls } from "three/addons/controls/OrbitControls.js";
    import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
    import { RectAreaLightHelper } from "three/examples/jsm/helpers/RectAreaLightHelper.js";
    import ThreeMeshUI from "three-mesh-ui";
    import { TransformControls } from "three/examples/jsm/controls/TransformControls.js";
    import { moveCartesian, setupSocket } from "$lib/robotics/laraapi";
    let ws: WebSocket;
    let ws_url = "ws://localhost:4245";
    let incoming_data: any;
    let update_from_server = true;
    //Enviroment Variable
    let canvas: HTMLCanvasElement;
    let scene: THREE.Scene;
    let camera: any;
    let renderer: THREE.WebGLRenderer;
    let animationId: number;
    let controls: OrbitControls;
    let resizeObserver: ResizeObserver;
    let container: HTMLDivElement;
    let transformControls : TransformControls;
    let clock: THREE.Clock;
    let stream: MediaStream | null = null;
    const position = new THREE.Vector3();
    const rotation = new THREE.Quaternion();

    function moveTo(vector: THREE.Vector3) {
        // Send the new position to the server
        const data = {
            type: 'move',
            position: {
                x: vector.x,
                y: vector.y,
                z: vector.z
            }
        };
        ws.send(JSON.stringify(data));
    }

    // function update(vector: THREE.Vector3){
    //     // Send the new position to the server
    //     // const data = {
    //     //     type: 'update',
    //     //     position: {
    //     //         x: vector.x,
    //     //         y: vector.y,
    //     //         z: vector.z
    //     //     }
    //     // };
    //     // if(ws){
    //     //     ws.send(JSON.stringify(data));
    //     // }
    //     moveCartesian(vector.x, vector.y, vector.z);
    // }
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

    onMount(() => {
        setupSocket();
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
        renderer.setSize(width, height);

        // Initialize controls
        controls = new OrbitControls(camera, renderer.domElement);
        controls.update();
        //add controls
        transformControls = new TransformControls(camera, renderer.domElement);
        transformControls.size = 0.75;
        transformControls.space = "world";
        scene.add(transformControls.getHelper());
        // transformControls.addEventListener("change", ()=>{
        //     // console.log("moved");
        //     // update(cube.position)

        // });
        transformControls.addEventListener("mouseDown", () => {
            controls.enabled = false;
        });
        transformControls.addEventListener("mouseUp", () => {
            controls.enabled = true;
        });
        // Create a cube and add it to the scene
        const geometry = new THREE.BoxGeometry(0.1, 0.1, 0.1);
        const material = new THREE.MeshBasicMaterial({ color: 0xf0ff0f });
        const cube = new THREE.Mesh(geometry, material);
        cube.position.set(-0.127,0.419,-0.52);
        scene.add(cube);
        transformControls.attach(cube);

        // Add lights
        addLights();
        // add gtlf model
        let gtlfloader = new GLTFLoader();
        gtlfloader.load("gtlf/GeneralScene.glb", (gltf) => {
            const model = gltf.scene;
            scene.add(model);
        });

        ws = new WebSocket(ws_url);

        ws.onopen = () => {
            console.log("WebSocket connection opened");
        };

        ws.onmessage = (event) => {
            try {
                incoming_data = JSON.parse(event.data);
                console.log(incoming_data)
                if (incoming_data.position) {
                    position.set(incoming_data.position.x, incoming_data.position.y, incoming_data.position.z);
                    console.log(position)
                }
                if (incoming_data.quaternion) {
                    rotation.set(incoming_data.quaternion.x, incoming_data.quaternion.y, incoming_data.quaternion.z, incoming_data.quaternion.w);
                    console.log(rotation)
                }

            } catch (e) {
                console.error("Error parsing JSON:", e);
            }
        };

        ws.onclose = () => {
            console.log("WebSocket connection closed");
        };

        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
        let temp = 0.7;
        let delta;
        function animate() {
            delta = clock.getDelta();
            ThreeMeshUI.update();
            // CanvasSizeHandler();
            cube.position.lerp(position, 0.1);
            cube.quaternion.slerp(rotation,  0.1);
            animationId = requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
            moveCartesian(cube.position.x, cube.position.y, cube.position.z);
        }
        stream = canvas.captureStream(30);
        
        animate();
    });

    onDestroy(() => {
        if (animationId) cancelAnimationFrame(animationId);
        if (resizeObserver) resizeObserver.disconnect();

        controls.dispose();
        renderer.dispose();
    });
</script>

<div
    bind:this={container}
    class="w-full h-800 relative"
>
    <canvas bind:this={canvas} class="block"></canvas>
</div>

<div class="mt-4">
    <pre class="bg-gray-100 p-4 rounded">
        {#if incoming_data}
            {JSON.stringify(incoming_data, null, 2)}
        {/if}
    </pre>
</div>
<button class="mt-4 px-4 py-2 bg-blue-500 text-white rounded" on:click={()=>{moveTo(new THREE.Vector3(0.5, 0.2, 0.5))}}>Move to A</button>
<button class="mt-4 px-4 py-2 bg-blue-500 text-white rounded" on:click={()=>{moveTo(new THREE.Vector3(0.5, 0.2, -0.5))}}>Move to B</button>
<button class="mt-4 px-4 py-2 bg-green-500 text-white rounded" on:click={() => {
    const randomX = Math.random(); // Random value between -5 and 5
    const randomZ = Math.random(); // Random value between -5 and 5
    moveTo(new THREE.Vector3(randomX, 0, randomZ));
}}>Move to Random Position</button>
