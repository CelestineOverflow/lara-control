import * as THREE from "three";
import { TransformControls } from "three/examples/jsm/controls/TransformControls.js";
export default class ObjectControl {
 constructor({ scene, camera, renderer, orbitControls, domElement }) {
   // Keep references to existing objects
   this.scene = scene;
   this.camera = camera;
   this.renderer = renderer;
   this.orbitControls = orbitControls;
   this.domElement = domElement; // typically renderer.domElement
   // Some internal helpers
   this.transformControls = null;
   this.raycaster = new THREE.Raycaster();
   this.mouse = new THREE.Vector2();
   this.createdObjects = [];
   this.selectedObject = null;
   this.isDragging = false;
   // Init transform controls
   this.initTransformControls();
   // Listen for pointer events (for picking) and transform changes
   this.addEventListeners();
 }
 initTransformControls() {
   // Set up TransformControls that attach to the existing camera & DOM
   this.transformControls = new TransformControls(this.camera, this.domElement);
   this.transformControls.addEventListener("change", () => {
     // Re-render if you want immediate visual updates
     this.renderer.render(this.scene, this.camera);
   });
   // If an object is currently being dragged, disable OrbitControls
   this.transformControls.addEventListener("dragging-changed", (event) => {
     // event.value === true means drag started
     this.orbitControls.enabled = !event.value;
     this.isDragging = event.value;
   });
   // Add the transform controls' helper to the scene
   this.scene.add(this.transformControls.getHelper());
 }
 addEventListeners() {
   // Listen for clicks (pointerup) to select objects
   this.domElement.addEventListener("pointerup", (e) => this.onPointerUp(e));
 }
 // Called when user pointer-ups on the scene
 onPointerUp(event) {
   // If transform is mid-drag, skip picking
   if (this.isDragging) return;
   // Convert pointer to normalized device coords
   const rect = this.domElement.getBoundingClientRect();
   this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
   this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
   this.raycaster.setFromCamera(this.mouse, this.camera);
   // Intersect with the scene children
   const intersects = this.raycaster.intersectObjects(this.scene.children, true);
   if (intersects.length === 0) return;
   // Filter out the gizmo handles
   const found = intersects.find((hit) => !this.isGizmoMesh(hit.object));
   if (!found) return;
   // If the clicked object is not in our managed collection, do nothing
   if (!this.createdObjects.includes(found.object)) return;
   // Otherwise, attach transform controls to that object
   this.selectedObject = found.object;
   this.transformControls.attach(this.selectedObject);
 }
 // Utility: check if object belongs to transform controls
 isGizmoMesh(obj) {
   // The transformControls have their own set of helper meshes parented to them
   return (
     obj.parent === this.transformControls ||
     obj.parent?.parent === this.transformControls ||
     obj.parent?.parent?.parent === this.transformControls
   );
 }
 // Create a new box and add to existing scene
 addBox(width = 1, height = 1, depth = 1) {
   const geometry = new THREE.BoxGeometry(width, height, depth);
   const material = new THREE.MeshPhongMaterial({ color: 0x44aa88 });
   const box = new THREE.Mesh(geometry, material);
   // Place at center (or wherever you wish)
   box.position.set(0, height / 2, 0);
   this.scene.add(box);
   this.createdObjects.push(box);
   // Select and attach transform controls to the new box
   this.selectedObject = box;
   this.transformControls.attach(this.selectedObject);
 }
 // Change transform mode: "translate", "rotate", "scale"
 setTransformMode(mode) {
   if (!this.transformControls) return;
   this.transformControls.setMode(mode);
 }
}