import URDFLoader, { type URDFRobot } from "urdf-loader";
import { Scene, LoadingManager, Quaternion, Vector3,SkinnedMesh,Skeleton,MeshPhongMaterial,CylinderGeometry,SkeletonHelper,Bone, PerspectiveCamera, BoxGeometry, MeshBasicMaterial, Mesh, CameraHelper, AxesHelper} from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { CCDIKSolver } from "three/examples/jsm/animation/CCDIKSolver.js";
import { toRad } from "./utils";

interface RobotJoint {
    name: string;
    value: number;
    set: (value: number) => void;
    add: (value: number) => void;
}

export class Lara {
    
    robot!: URDFRobot;
    loaded = false;
    joint1: RobotJoint;
    joint2: RobotJoint;
    joint3: RobotJoint;
    joint4: RobotJoint;
    joint5: RobotJoint;
    joint6: RobotJoint;
    mesh : SkinnedMesh | undefined;
    bone0 : any;
    bone1 : any;
    bone2 : any;
    bone3 : any; 
    rootBone : any;
    targetBone :any;
    skeleton : any;
    iks : any;
    ikSolver : any;
    camera : PerspectiveCamera | undefined;
    camera_helper : CameraHelper | undefined;
    helper : any;
    constructor(scene: Scene) {
        // Initialize joints with their names and default values
        this.joint1 = { name: "lara10_joint1", value: toRad(0), set: () => {}, add: () => {} };
        this.joint2 = { name: "lara10_joint2", value: toRad(0), set: () => {}, add: () => {} };
        this.joint3 = { name: "lara10_joint3", value: toRad(0), set: () => {}, add: () => {} };
        this.joint4 = { name: "lara10_joint4", value: toRad(0), set: () => {}, add: () => {} };
        this.joint5 = { name: "lara10_joint5", value: toRad(90), set: () => {}, add: () => {} };
        this.joint6 = { name: "lara10_joint6", value: toRad(-90), set: () => {}, add: () => {} };

        const manager = new LoadingManager();
        const loader = new URDFLoader(manager);

        loader.load("urdf/lara10/lara10.urdf", (result: any) => {
            this.robot = result;
            console.log("Loaded model");
        });

        manager.onLoad = () => {
            this.robot.updateMatrixWorld(true);
            this.robot.rotation.x = -Math.PI / 2;
            scene.add(this.robot);
            // console.log(this.robot);

            // Function to recursively find all meshes
            const findMeshes = (object: any) => {
                let meshes: any[] = [];
                object.traverse((child: any) => {
                    if (child.isMesh) {
                        meshes.push(child);
                    }
                });
                return meshes;
            };

            const meshes = findMeshes(this.robot);

            console.log("Found meshes:", meshes);
            if (meshes.length > 0) {
                const lastMesh = meshes[meshes.length - 1];
                //new material
                const material = new MeshPhongMaterial({
                    color: 0x156289,
                    emissive: 0x072534,
                    flatShading: true,
                });
                lastMesh.material = material;
                // lastMesh.add(cube);
                let gtlfloader = new GLTFLoader();
                gtlfloader.load("gtlf/plunger.glb", (gltf) => {
                    const model = gltf.scene;
                    model.position.set(0, -0.17, 0);
                    model.rotation.set(0, 0, 0);
                    lastMesh.add(model);
                    //add camera
                    this.camera = new PerspectiveCamera(60, 1, 0.01, 1000);
                    this.camera_helper = new CameraHelper(this.camera);
                    scene.add(this.camera_helper);
                    lastMesh.add(this.camera);
                    //move camera relative to the robot down y axis
                    this.camera.position.set(0, -0.27, -0.02);
                    //rotate camera to look straight down
                    this.camera.rotation.set(toRad(-90), 0, 0);
                    //add axis helper to the end effector for visual aid
                    const axesHelper = new AxesHelper( .5 )
                    //move the axis helper to the end effector
                    axesHelper.position.set(0, -.2, 0);
                    lastMesh.add(axesHelper);
                });
            
            }
            
            console.log("Loaded robot model");
            this.loaded = true;

            // Assign the set and add methods to each joint
            this.assignSetMethod(this.joint1);
            this.assignSetMethod(this.joint2);
            this.assignSetMethod(this.joint3);
            this.assignSetMethod(this.joint4);
            this.assignSetMethod(this.joint5);
            this.assignSetMethod(this.joint6);

            this.assignAddMethod(this.joint1);
            this.assignAddMethod(this.joint2);
            this.assignAddMethod(this.joint3);
            this.assignAddMethod(this.joint4);
            this.assignAddMethod(this.joint5);
            this.assignAddMethod(this.joint6);
        };
        const geometry = new CylinderGeometry(1, 1, 20, 8, 1, false);
        const material = new MeshPhongMaterial({
            color: 0x156289,
            emissive: 0x072534,
            flatShading: true,
        });
        //
        let bones = [];
        // "root"
        this.rootBone = new Bone();
        this.rootBone.position.y = 0;
        bones.push(this.rootBone);

        this.bone0 = new Bone();
        this.bone0.position.y = 0.0;
        this.rootBone.add(this.bone0);
        bones.push(this.bone0);
        // bone 1
        this.bone1 = new Bone();
        this.bone1.position.y = 0.26;
        this.bone0.add(this.bone1);
        bones.push(this.bone1);
        // bone 2
        this.bone2 = new Bone();
        this.bone2.position.y = 0.4799999999967618;
        this.bone1.add(this.bone2);
        bones.push(this.bone2);
        // bone 3
        this.bone3 = new Bone();
        this.bone3.position.y = 0.5199999999964918;
        this.bone2.add(this.bone3);
        bones.push(this.bone3);
        // "target"
        this.targetBone = new Bone();
        this.targetBone.position.y = 0.25;
        this. targetBone.position.z = 0.15;
        this.rootBone.add(this.targetBone);
        bones.push(this.targetBone);
        //
        this.mesh = new SkinnedMesh(geometry, material);
        this.skeleton = new Skeleton(bones);

        this.mesh.add(bones[0]); // "root" bone
        this.mesh.bind(this.skeleton);

        //
        // ikSolver
        //

        this.iks = [
            {
                target: 5, // "target"
                effector: 4,
                links: [
                    {
                        index: 3,
                        rotationMin: new Vector3(-3, 0, 0),
                        rotationMax: new Vector3(3, 0, 0),
                    },
                    {
                        index: 2,
                        rotationMin: new Vector3(-3, 0, 0),
                        rotationMax: new Vector3(3, 0, 0),
                    },
                    {
                        index: 1,
                        rotationMin: new Vector3(0, -3, 0),
                        rotationMax: new Vector3(0, 3, 0),
                    },
                ],
            },
        ];

        this.ikSolver = new CCDIKSolver(this.mesh, this.iks);
        this.helper = new SkeletonHelper(this.mesh);
        scene.add(this.helper);
    }

    private assignAddMethod(joint: RobotJoint) {
        joint.add = (value: number) => {
            if (!this.loaded) {
                console.error("Lara not loaded yet");
                return;
            }
            joint.value += value;
            this.moveJoint(joint.name, joint.value);
        };
    }

    private assignSetMethod(joint: RobotJoint) {
        joint.set = (value: number) => {
            if (!this.loaded) {
                console.error("Lara not loaded yet");
                return;
            }
            joint.value = value;
            this.moveJoint(joint.name, value);
        };
    }

    private moveJoint(jointName: string, value: number) {
        if (!this.loaded) {
            console.error("Lara not loaded");
            return;
        }
        try {
            if (this.robot.joints[jointName]) {
                // console.log("Setting joint " + jointName + " to value " + value);
                this.robot.joints[jointName].setJointValue(value);
            } else {
                console.error("Joint not found: " + jointName);
            }
        } catch (error) {
            console.error("Error moving joint: " + jointName, error);
        }
    }

    public getLinkMatrix(linkname : string){
        const EndActuatorMatrix = this.robot.links[linkname].matrixWorld;
        const Quat = new Quaternion();
        const Pos = new Vector3();
        EndActuatorMatrix.decompose(
            Pos,
            Quat,
            new Vector3(),
        );
        return{Quat, Pos}
    }

    public update() {
        this.targetBone.updateMatrixWorld(true);
        this.ikSolver.update();
        this.joint1.set(this.bone0.rotation.y + toRad(-90));
        this.joint2.set(this.bone1.rotation.x);
        this.joint3.set(this.bone2.rotation.x);
    }
    public async moveRealRobot() {
        console.log("trying to move robot arm");
        const url = "http://192.168.2.209:1442/pose";
        const data = {
            joint1: this.joint1.value,
            joint2: this.joint2.value,
            joint3: this.joint3.value,
            joint4: this.joint4.value,
            joint5: this.joint5.value,
            joint6: this.joint6.value,
        };
    
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log("Robot moved successfully:", result);
        } catch (error) {
            console.error("Error moving the robot:", error);
        }
    }
}