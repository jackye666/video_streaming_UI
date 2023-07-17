import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';


var position_init = {}
var rotation_init = {};
var scene = new THREE.Scene(); 
var pi = 3.14;
 // Load Camera Perspektive
var camera = new THREE.PerspectiveCamera( 100, window.innerWidth / window.innerHeight, 0.1, 20000 );
// camera.position.set( 0, 0, 30 );

// $("#canvas-container canvas").css({
//     "display": "block",
//     "width": "50%",
//     "height": "50%",
//     "margin-top": "20%",
//     "margin-left": "20%",
// });


camera.aspect = 0.8;
camera.updateProjectionMatrix();

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





$("#canvas-container canvas").css({
    "display": "block",
    "width": "50%",
    "height": "50%",
    "margin-top": "20%",
    "margin-left": "20%",
});

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



object.rotation.x = -pi/2;
// object.rotation.z = (55)/180*pi;
object.rotation.z = pi/2;
object.position.y = 150;
// object.rotation.y = -pi/2;
// object.rotation.y = pi;
position_init = JSON.parse(JSON.stringify(object.position));
console.log(position_init);
rotation_init = JSON.parse(JSON.stringify(object.rotation));
render();
animate();
});	 
// camera.rotation.y= pi/2;
// camera.rotation.x= pi/2;

function animate() {
    render();
    requestAnimationFrame( animate );
    }

var mv_pred = "hold";
var updated = false;
setInterval(()=>{
    $.ajax({
        url:"/move_prediction",
        method:"GET",
        success: function(response){
            console.log("3d move is "+ response);
            mv_pred = response;
            updated = true;
        }
    });
},3000);
var prev = "hold";

// var axises = ["x","y","z"];

// function update_pos_rot(){
//     for(let axis of axises){
//         object.rotation[axis] = rotation_init[axis];
//         object.position[axis] = position_init[axis];
//     }
// };

var coordinate_map={
    "x":{"axis":"x","c":"a","a":"c"}

}
var cnt = 0;

function render() {
    // mv_pred = "hold";
    switch(mv_pred){
        case "x+":
        case "x-":
        case "y+":
        case "y-":
        case "z+":
        case "z-":
            var axis = mv_pred[0];
            var dir = mv_pred[1] == "+" ? 1:-1;
            console.log("axis is "+axis, "dir is "+dir);
            if(updated && prev!= "hold"){
                console.log("prev",object.position);
                object.position[prev[0]] = position_init[prev[0]];
                // update_pos_rot();
                updated =false;
                console.log("updated",object.position);
                
            }
            object.position[axis] += dir*0.1;
            if (dir*(object.position[axis] - position_init[axis]) >= 50){
                object.position[axis] = position_init[axis];
            }
            prev = mv_pred;
            break;

        case "x_a":
        case "x_c":
        case "y_a":
        case "y_c":
        case "z_a":
        case "z_c":
            var raw_axis = mv_pred[0];
            var raw_dir = mv_pred[2];
            var axis = coordinate_map[raw_axis].axis;
            var dir = coordinate_map[raw_axis][raw_dir] == "c" ? 1:-1;

            console.log("axis is "+axis, "dir is "+dir);
            if(updated && prev!= "hold"){
                console.log("prev",object.position);
                // update_pos_rot();
                // var axises = ["x","y","z"];
                // for(let axis of axises){
                //     object.rotation[axis] = rotation_init[axis];
                //     object.position[axis] = position_init[axis];
                // }

                updated =false;
                console.log("updated",object.position, object.rotation);
                // object.rotation[axis] = rotation_init[axis] - dir*pi/6;
                
            }
            
            object.rotation[axis] += dir*pi/1000;
            cnt++;
            if(cnt >= 20){
                console.log("rotation:",object.rotation,"init:",rotation_init.x);
                cnt = 0;
            }
            // if (Math.abs(object.rotation[axis] - rotation_init[axis]) >= pi/6){
            //     object.rotation[axis] = rotation_init[axis];
            // }
            prev = mv_pred;
            break;
        case "hold":
            // object.position = JSON.parse(JSON.stringify(position_init));
            // object.rotation = {...rotation_init};
            // update_pos_rot();
    }    

        renderer.render( scene, camera );
    };

// render();
// animate(); 
