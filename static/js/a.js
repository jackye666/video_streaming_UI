// Movement Helpers
var LEFT = false;
var RIGHT = false;
var UP = false;
var DOWN = false;
var RISE = false;
var FALL = false;
name_lst = ["PLAX","PSAX","AP"]
var img_lst;
var cur_id = 0;
var name_id = 0;

let meter = document.getElementById("meter");
meter.style.strokeDashoffset = 360;
function updateHTMLProgress(value) {
    
    const maxOffset = 360; // Maximum stroke-dashoffset value
    const offset =  meter.style.strokeDashoffset - value/100 * maxOffset;
    if(offset < 0){
        offset = offset%360+360;
    }
    // console.log(offset);
    meter.style.strokeDashoffset = offset; 
    $(".score").text(100 - Math.round(100 * offset/360)+5);
}

function isMouseOverElement(event, element) {
    var mouseX = event.pageX;
    var mouseY = event.pageY;
    var offset = element.offset();
    var elementX = offset.left;
    var elementY = offset.top;
    var elementWidth = element.outerWidth();
    var elementHeight = element.outerHeight();

    // console.log(mouseX,mouseY,elementX,elementY,elementWidth,elementHeight);

    return (
      mouseX >= elementX &&
      mouseX <= elementX + elementWidth &&
      mouseY >= elementY &&
      mouseY <= elementY + elementHeight
    );
  }


  function sleep(milliseconds) {
    const startTime = Date.now();
    const endTime = startTime + milliseconds;
    let currentTime = startTime;
  
    while (currentTime < endTime) {
      currentTime = Date.now();
    }
  }
  
meter_id = 0
function startUpdateScore(){
    meter.style.strokeDashoffset = 360;
    document.getElementById("bg-circle").style.fill = "#897b66";
    meter_id = setInterval(updateScore, 50);
}

function updateScore(){
    if(meter.style.strokeDashoffset/360 > 0.6)
        updateHTMLProgress(1);
    else{
        let p = Math.random();
        if(p > 0.7){
            updateHTMLProgress(-1);
        }
        else{
            updateHTMLProgress(1);
        }
    }
    if(meter.style.strokeDashoffset < 30){
        clearInterval(meter_id);
        // alert("Perfect ultrasound Imaging");
        // sleep(3000);
        const imageElement = document.getElementById('camera_id');
        Object.defineProperty(imageElement, 'src', {
            writable: false,
            configurable: false
        });
        document.getElementById("bg-circle").style.fill = "rgb(195,162,111)";
        setTimeout(()=>{
            startUpdateScore();
        },3000);

    }
}



$(document).ready(function(){
    $(window).resize(function(){
        console.log("resize!")
        window.resizeTo(1300,780);
        console.log("restored!")
    });
    $.ajax({
        url: "/img_name",
        method: "GET",
        dataType: "json",
        success: function(response){
            console.log(response[name_lst[1]]);
            // console.log(response[name_lst[0]])
            img_lst = response;

        },
        error: function(err){
            console.log(err);
        }
    });


    //plus and minus sign
    var click_delay = 50;

    var cnt_depth = $('#depth .count');
    let plus_id = 0,minus_id = 0;
    $('#depth .plus').mousedown(function(){
        console.log("mousedown");
        let str = parseInt(cnt_depth.text());
        plus_id = setInterval(()=>{
            str++;
            cnt_depth.text(str+"cm");
            console.log("plus");
        },click_delay)
    })
    $('#depth .plus').mouseup(()=>{
        console.log("mouseup");
        clearInterval(plus_id);
        console.log("cleared interval");
    });
    $('#depth .plus').mouseleave(()=>{
        console.log("mouseleave");
        clearInterval(plus_id);
        console.log("cleared interval");
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
    })
    $('#depth .minus').mouseup(()=>{
        console.log("mouseup");
        clearInterval(minus_id);
    });
    $('#depth .minus').mouseleave(()=>{
        console.log("mouseleave");
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
    })
    $('#gain .plus').mouseup(()=>{
        clearInterval(plus_id);
    });
    $('#gain .plus').mouseleave(()=>{
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
    })

    $('#gain .minus').mouseup(()=>{
        clearInterval(minus_id);
    });
    $('#gain .minus').mouseleave(()=>{
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

    // let l = img_lst.position;
    $("#toright").click(()=>{
        let data = img_lst[name_lst[name_id]];
        if(cur_id < data.position.length-1){
            cur_id+=1;
        }
        
        let fname1 = "static/img/"+data.diagram[cur_id]+".png";
        let fname2 = 'static/img/'+data.position[cur_id]+".png";
        $("#img_dig").attr("src",fname1);
        $("#img_pos").attr("src",fname2);
        let topic = $(".setting_topics h3");
        let subtitle = $(".setting_topics .bt-select span");
        
        topic.text(data.category[cur_id]);
        let tmp = (cur_id+1) + " of "+data.position.length+", Next "+ data.category[cur_id+1];
        subtitle.text(tmp);

    });

    $("#toleft").click(()=>{
        let data = img_lst[name_lst[name_id]];
        if(cur_id > 0){
            cur_id -= 1;
        }
        let fname1 = "static/img/"+data.diagram[cur_id]+".png";
        let fname2 = 'static/img/'+data.position[cur_id]+".png";
        $("#img_dig").attr("src",fname1);
        $("#img_pos").attr("src",fname2);
        let topic = $(".setting_topics h3");
        let subtitle = $(".setting_topics .bt-select span");
        
        topic.text(data.category[cur_id]);
        let tmp = (cur_id+1) + " of "+data.position.length+", Next "+ data.category [cur_id+1];
        subtitle.text(tmp);
    });


    $("#dropdown").mouseover(()=>{
        $(".dropdown-content").show();
        let h = $(".setting_header").height();
        $(".dropdown-content").css("top",h-2+"px");
    });
    $("#dropdown").mouseleave((event)=>{
        if(!isMouseOverElement(event,$(".dropdown-content"))){
            console.log("dropdown");
            $(".dropdown-content").hide();
        }
    });
    $(".dropdown-content").mouseleave((event)=>{
        let in_sub = isMouseOverElement(event,$(".PLAX"))||isMouseOverElement(event,$(".PSAX"))||isMouseOverElement(event,$(".AP"))
        // var in_sub= false;
        // $(".subdropdown").each((in_sub)=>{
        //     in_sub = in_sub || isMouseOverElement(event,$(this));
        //     return in_sub
        // })
        console.log(in_sub);
        if(!isMouseOverElement(event,$("#dropdown")) && !in_sub){
            // console.log("dropdown-content leave",isMouseOverElement(event,$("#dropdown")),isMouseOverElement(event,$(".subdropdown")));
            
            $(".dropdown-content").hide();
            $(".subdropdown").hide();
        }
    });

    $(".dropdown-content a").mouseover((event)=>{
        $(".subdropdown").hide();
        console.log(event.target);
        let name = event.target.id;
        $("."+name).show();
        let offset = $("#"+name).offset();
        $("."+name).css("top",offset.top+"px");
        $("."+name).css("right",offset.right-3+"px");
    })

    $(".dropdown-content a").mouseleave((event)=>{
        let name = event.target.id;
        console.log("leave a:",name);
        if(!isMouseOverElement(event,$("."+name))){
            console.log("hide sub "+name)
            $("."+name).hide();
        }
    })

    $(".subdropdown").mouseleave((event)=>{
        
        if(!isMouseOverElement(event,$(".dropdown-content"))){
            console.log("sub hide");
            $(".subdropdown").hide();
            $(".dropdown-content").hide();
        }
    });

    $(".subdropdown a").click((event)=>{
        // console.log(event.target.text);
        // console.log($(this))
        let txt = event.target.text;
        if(txt.substr(0,2) == "AP"){
            name_id = name_lst.indexOf("AP");
        }
        else if(txt.substr(0,4) == "PLAX"){
            name_id = name_lst.indexOf("PLAX");
        }
        else{
            name_id = name_lst.indexOf("PSAX");
        }
        let data = img_lst[name_lst[name_id]];
        // console.log(data,name_id,name_lst)
        cur_id = data.category.indexOf(txt);
        
        let fname1 = "static/img/"+data.diagram[cur_id]+".png";
        let fname2 = 'static/img/'+data.position[cur_id]+".png";
        $("#img_dig").attr("src",fname1);
        $("#img_pos").attr("src",fname2);
        let topic = $(".setting_topics h3");
        let subtitle = $(".setting_topics .bt-select span");
        
        topic.text(data.category[cur_id]);
        let tmp = (cur_id+1) + " of "+data.position.length+", Next "+ data.category [cur_id+1];
        subtitle.text(tmp);

        $(".subdropdown,.dropdown-content").hide();
    });


    $(".save-page button").click(()=>{
        $.ajax({
            url: "/save_img",
            method:"GET",
            success: function(response){
                alert("Frame Saved!");
            }
        });
    });



    startUpdateScore();

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