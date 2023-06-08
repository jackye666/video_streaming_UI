// Movement Helpers
var LEFT = false;
var RIGHT = false;
var UP = false;
var DOWN = false;
var RISE = false;
var FALL = false;

var img_lst;



$(document).ready(function(){
    $.ajax({
        url: "/img_name",
        method: "GET",
        dataType: "json",
        success: function(response){
            console.log(response);
            console.log(response.name,response.name.length)
            img_lst = response;
        },
        error: function(err){
            console.log(err);
        }
    });


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

    var cur_id = 0;
    // let l = img_lst.position;
    $("#toright").click(()=>{
        if(cur_id < img_lst.position.length-1){
            cur_id+=1;
        }
        
        let fname1 = "static/img/"+img_lst.diagram[cur_id]+".png";
        let fname2 = 'static/img/'+img_lst.position[cur_id]+".png";
        $("#img_dig").attr("src",fname1);
        $("#img_pos").attr("src",fname2);
        let topic = $(".setting_topics h3");
        let subtitle = $(".setting_topics .bt-select span");
        
        topic.text(img_lst.name[cur_id]);
        let tmp = (cur_id+1) + " of "+img_lst.position.length+", Next "+ img_lst.name[cur_id+1];
        subtitle.text(tmp);

    })

    $("#toleft").click(()=>{
        if(cur_id > 0){
            cur_id -= 1;
        }
        let fname1 = "static/img/"+img_lst.diagram[cur_id]+".png";
        let fname2 = 'static/img/'+img_lst.position[cur_id]+".png";
        $("#img_dig").attr("src",fname1);
        $("#img_pos").attr("src",fname2);
        let topic = $(".setting_topics h3");
        let subtitle = $(".setting_topics .bt-select span");
        
        topic.text(img_lst.name[cur_id]);
        let tmp = (cur_id+1) + " of 5, Next "+ img_lst.name [cur_id+1];
        subtitle.text(tmp);
    })

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