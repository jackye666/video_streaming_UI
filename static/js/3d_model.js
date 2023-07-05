import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';


var scene = new THREE.Scene(); 
var pi = 3.14;
 // Load Camera Perspektive
var camera = new THREE.PerspectiveCamera( 90, window.innerWidth / window.innerHeight, 0.1, 20000 );
// camera.position.set( 0, 0, 30 );

 // Load a Renderer
var renderer = new THREE.WebGLRenderer({ alpha: true });
// renderer.setClearColor( 0xC5C5C3 );
renderer.setClearColor( 0x000000,0 );
renderer.setPixelRatio( window.devicePixelRatio );
// renderer.setSize(window.innerWidth, window.innerHeight);
var width;
var height;
width = $("#canvas-container").width();
height = $("#canvas-container").height();
renderer.setSize(width, height);
console.log(width,height);
document.getElementById("canvas-container").appendChild(renderer.domElement);
// document.body.appendChild(renderer.domElement);

 // Load the Orbitcontroller
// var controls = new OrbitControls( camera, renderer.domElement ); 

 // Load Light
// var ambientLight = new THREE.AmbientLight( 0xcccccc );
// scene.add( ambientLight );
    
// var directionalLight = new THREE.DirectionalLight( 0xffffff );
// directionalLight.position.set( 0, 1, 1 ).normalize();
// scene.add( directionalLight );	

// Create an ambient light
const ambientLight = new THREE.AmbientLight(0xffffff, 1 ); // Color: white, Intensity: 0.5
scene.add(ambientLight);

// Create directional lights
const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.5); // Color: white, Intensity: 0.5
directionalLight1.position.set(1, 1, 1); // Set position
scene.add(directionalLight1);

const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5); // Color: white, Intensity: 0.5
directionalLight2.position.set(-1, -1, -1); // Set position
scene.add(directionalLight2);

// $(document).ready(function(){
//      $("canvas").css({"height":"50%"});
// })
 // glTf 2.0 Loader
var object;
var loader = new GLTFLoader();				
loader.load( 'static/3d_model/probe_cut_axis.gltf', function ( gltf ) {             
object = gltf.scene;	
// console.log(object.position);			
object.scale.set( 2, 2, 2 );	
object.position.set(0,0,0);		   


scene.add( gltf.scene );
renderer.render(scene, camera);

const modelBoundingBox = new THREE.Box3().setFromObject(object);
const modelCenter = modelBoundingBox.getCenter(new THREE.Vector3());
const modelSize = modelBoundingBox.getSize(new THREE.Vector3());

// Calculate a distance based on the size of the model
const cameraDistance = Math.max(modelSize.x, modelSize.y, modelSize.z) * 1.2;

camera.position.set(modelCenter.x, modelCenter.y, modelCenter.z + cameraDistance);
// camera.position.set(modelSize.x/2,modelSize.y/2,modelCenter.z/2+cameraDistance)
console.log(modelCenter);
// camera.lookAt(new THREE.Vector3(modelCenter.x-modelSize.y/2,modelCenter.y+modelSize.y/2,modelCenter.z));
camera.lookAt(modelCenter);
// camera.lookAt(new THREE.Vector3(0,0,cameraDistance));
// const translationVector = new THREE.Vector3();
// translationVector.subVectors(new THREE.Vector3(0, 0, 0), modelCenter);

// // Step 3: Apply the translation to the model's position
// object.position.add(translationVector);
// camera.rotation.y = pi/2+0.3;
console.log(object.position)

// object.rotation.x = pi/2;
// object.rotation.z = (55)/180*pi;
// object.position.y += 200;
// object.rotation.y = pi;
render();
animate();
});	 
camera.rotation.y= pi/2;
// camera.rotation.x= pi/2;

function animate() {
    render();
    requestAnimationFrame( animate );
    }

function render() {
    
    object.rotation.z+=0.01;
    // object.rotation.y+=0.01;

    // camera.rotation.y -= pi/2*0.005;
    // console.log(camera.rotation.x,camera.rotation.y,camera.rotation.z);
    // object.position.z -= 0.1;
    // if(object.position.z < -10){
    //     object.position.z = 10;
    // }
    // // camera.rotation.y+= pi/180;
    // object.position.x += 0.05;
    renderer.render( scene, camera );
    }

// render();
// animate(); 
