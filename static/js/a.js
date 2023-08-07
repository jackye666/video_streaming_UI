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
    const offset =  360- value/100 * maxOffset;
    // console.log(offset);
    meter.style.strokeDashoffset = offset; 
    $(".score").text(value);
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



    $("#save-btn").click(()=>{
        var button = $(this);

        button.prop('disabled', true);
        button.text('Saving...');

        $.ajax({
            url: "/save_img",
            method:"GET",
            success: function(response){
                alert("Frame Saved!");
                // $(this).button("reset");
            }
        });
    });

    // var quality_score = 0;
    setInterval(()=>{
        $.ajax({
            url:"/get_score",
            method:"GET",
            success: function(response){
                // console.log("score is "+ response);
                updateHTMLProgress(parseFloat(response));
            }
        });
    },50);
    let shining_id = 0; 
    setInterval(()=>{
        $.ajax({
            url:"/move_prediction",
            method:"GET",
            success: function(response){
                // console.log("score is "+ response);
                clearInterval(shining_id);
                $("#x0").attr("src",`static/3d_arrow/x-.png`);
                $("#x1").attr("src",`static/3d_arrow/x+.png`);
                $("#y0").attr("src",`static/3d_arrow/y-.png`);
                $("#y1").attr("src",`static/3d_arrow/y+.png`);
                if(response!="hold"){
                    console.log(response[1],response);
                    let id = "";
                    if(response[1]=="+"){
                        id=response[0]+1;
                    }
                    else{
                        id=response[0]+0;
                    }
                    $(`#${id}`).attr("src",`static/3d_arrow/${response}shining.png`);
                    let shine = false;
                    shining_id = setInterval(()=>{
                        if(shine){
                            shine = false;
                            $(`#${id}`).attr("src",`static/3d_arrow/${response}shining.png`);
                        }
                        else{
                            shine = true;
                            $(`#${id}`).attr("src",`static/3d_arrow/${response}.png`);
                        }
                    },500);
                    // $(`#${id}`).attr("src",`static/3d_arrow/${response}mv.png`);
                    // $(`#x0`).attr("src",`static/3d_arrow/test.png`);
                }     
            }
        });
    },3000);

    $(".camera").on("load",function(){
        var vleft = $(".camera").position().left+1;
        var vtop = $(".camera").position().top-1;
        var height = $(".camera").height()*0.3;
        console.log(vleft,vtop);
        $(".gif").css({
            "left":vleft,
            "top":vtop,
            "height":`${height}px`
        })
        w = $(".camera").width();
        h = $(".camera").height();
        height = $(".camera").height()*0.04;
        // console.log(vleft,vtop);
        $("#x0").css({
            "left":vleft+w*0.07,
            "top":vtop+h*0.14,
            "height":`${height}px`
        });
        $("#x1").css({
            "left":vleft+w*0.23,
            "top":vtop+h*0.14,
            "height":`${height}px`
        });
        $("#y0").css({
            "left":vleft+w*0.165,
            "top":vtop+h*0.20,
            "width":`${height}px`
        });
        $("#y1").css({
            "left":vleft+w*0.165,
            "top":vtop+h*0.04,
            "width":`${height}px`
        });
    });



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