// Movement Helpers
var LEFT = false;
var RIGHT = false;
var UP = false;
var DOWN = false;
var RISE = false;
var FALL = false;



$(document).ready(function(){
    //plus and minus sign

    var click_delay = 50;

    var cnt_depth = $('#depth .count')
    $('#depth .plus').mousedown(function(){
        console.log("mousedown");
        let str = parseInt(cnt_depth.text());
        plus_id = setInterval(()=>{
            str++;
            cnt_depth.text(str+"cm");
            console.log("plus");
        },click_delay)
    }).mouseup(()=>{
        console.log("mouseup");
        clearInterval(plus_id);
    });

    $('#depth .minus').mousedown(()=>{
        console.log("mousedown");
        let str = parseInt(cnt_depth.text());
        minus_id = setInterval(()=>{
            str--;
            if(str<0){
                str=0;
                clearInterval(minus_id);
            }
            cnt_depth.text(str+"cm");
            console.log("minus");
        },click_delay)
    }).mouseup(()=>{
        console.log("mouseup");
        clearInterval(minus_id);
    });

    var cnt_gain = $('#gain .count')
    $('#gain .plus').mousedown(()=>{
        let str = parseInt(cnt_gain.text());
        plus_id = setInterval(()=>{
            str++;
            if(str>100){
                str=100;
                clearInterval(plus_id);
            }
            cnt_gain.text(str+"%");
        },click_delay)
    }).mouseup(()=>{
        clearInterval(plus_id);
    });

    $('#gain .minus').mousedown(()=>{
        let str = parseInt(cnt_gain.text());
        minus_id = setInterval(()=>{
            str--;
            if(str<0){
                str=0;
                clearInterval(minus_id);
            }
            cnt_gain.text(str+"%");
        },click_delay)
    }).mouseup(()=>{
        clearInterval(minus_id);
    });

    setInterval(()=>{
        if(LEFT){
            console.log("left");
        }
        if(RIGHT){
            console.log("right");
        }
        if(UP){
            console.log("up");
        }
        if(DOWN){
            console.log("down");
        }
        if(RISE){
            console.log("rise");
        }
        if(FALL){
            console.log("fall");
        }
    },100);


 });



 // Keydown event handler

document.onkeydown = function(e) {
    if (e.key == 'ArrowLeft') LEFT = true;
    if (e.key == 'ArrowRight') RIGHT = true;
    if (e.key == 'ArrowUp') UP = true;
    if (e.key == 'ArrowDown') DOWN = true;
    if (e.key == 'r') RISE = true;
    if (e.key == 'f') FALL = true;
}

// Keyup event handler
document.onkeyup = function (e) {
    if (e.key == 'ArrowLeft') LEFT = false;
    if (e.key == 'ArrowRight') RIGHT = false;
    if (e.key == 'ArrowUp') UP = false;
    if (e.key == 'ArrowDown') DOWN = false;
    if (e.key == 'r') RISE = false;
    if (e.key == 'f') FALL = false;
}