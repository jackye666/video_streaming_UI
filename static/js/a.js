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
// meter.style.strokeDashoffset = 326;
// $("#add").click(function(){
//     value = $(".score").text();
//     value =parseInt(value);
//     value+=1;
//     if(value <= 0) value = 0;
//     if(value >= 100) value = 100;
//     updateHTMLProgress(value);
// });
// $("#minus").click(function(){
//     value = $(".score").text();
//     value =parseInt(value);
//     value-=1;
//     if(value <= 0) value = 0;
//     if(value >= 100) value = 100;
//     updateHTMLProgress(parseInt(value));
// });
function updateHTMLProgress(value) {
    const maxOffset = 326; // Maximum stroke-dashoffset value
    const offset =  maxOffset- (value)/100 * maxOffset;
    $(".score").text(value);
    // console.log(offset);
    meter.style.strokeDashoffset = offset; 
    if(value <= 30 ){
        meter.style.stroke = '#C51605';
    }
    else if(value <= 55){
        meter.style.stroke = '#FD8D14';
    }
    else if(value <= 85 ){
        meter.style.stroke = '#FFE17B';
    }
    else{
        meter.style.stroke = '#A2FF86';
        meter.style.strokeDashoffset = 0; 
    }
    
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
        var button = $("#save-btn");

        // button.prop('disabled', true);
        button.text('Saving...');

        $.ajax({
            url: "/save_img",
            method:"GET",
            success: function(response){
                alert("Frame Saved!");
                console.log(response,`<div><img src='${response}'></div>`);
                button.text('Save');
                // $('.image-container').append(`<div><img src="static/saved_frame/frame_131.jpg" alt="Image 1"></div>`);
                $('.image-container').append(`<div class="image-border"><img class="image-saved" src="${response}"></div>`);
                // $(".image-container div img").hover(function() {
                //     $(this).css("transform", "scale(1.05)");
                //   }, function() {
                //     $(this).css("transform", "scale(1)");
                //   });
            }
        });
    });
    var pause_btn_status = 0;
    $("#pause-btn").click(()=>{
        // var myVariable = "Hello from front-end!"; 
        var button = $("#pause-btn");
        $.ajax({
            url:"/pause",
            method:"POST",
            data:{ispause: pause_btn_status},
            success:function(response){
                console.log("pause btn op:",response);       
                pause_btn_status = 1-pause_btn_status;
                if(pause_btn_status == 0){
                    console.log("pause_btn_status:",pause_btn_status);
                    button.text("Pause");
                }
                else{
                    console.log("pause_btn_status:",pause_btn_status);
                    button.text("Resume");
                }         
            }
        })
    });

    $(".image-container").on("click",".image-saved",function() {
        // 在控制台输出被点击的图片的src属性
        var clickedSrc = $(this).attr("src");
        console.log("Clicked image src:", clickedSrc);
        alert(clickedSrc);
        // $(".modal").css({
        //     "display":"flex",
        //     "z-index":"10"
        // });
        // $(".modal-image").attr("src",clickedSrc);
        // $(".modal-image").css("transform","scale(1)");
        // setTimeout(() => {
        //     $(".modal-image").css("transform","scale(1)");
        // }, 10);
    });
    // $(".modal").click(()=>{
    //     $(this).css({"display":"none","z-index":"0"});
    // })
    // var quality_score = 0;
    setInterval(()=>{
        $.ajax({
            url:"/get_score",
            method:"GET",
            success: function(response){
                // console.log("score is "+ response);
                // response = 0;
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
                $(`.gif`).attr("src",`static/3d_img/hold.png`);
                // $("#x0").attr("src",`static/3d_arrow/x-.png`);
                // $("#x1").attr("src",`static/3d_arrow/x+.png`);
                // $("#y0").attr("src",`static/3d_arrow/y-.png`);
                // $("#y1").attr("src",`static/3d_arrow/y+.png`);
                $(".arrow_3d").hide();
                if(response!="hold"){
                    if(response[1] != "_"){
                        // console.log(response[1],response);
                        let id = "";
                        if(response[1]=="+"){
                            id=response[0]+1;
                        }
                        else{
                            id=response[0]+0;
                        }
                        // $(`#${id}`).attr("src",`static/3d_arrow/${response}shining.png`);
                        $(`#${id}`).attr("src",`static/3d_arrow/${response}.png`);
                        $(`#${id}`).show();
                        let shine = true;
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
                    }
                    else{
                        $(".arrow_3d").hide();
                        $(`.gif`).attr("src",`static/3d_img/${response}_arrow.png`);
                        let shine = false;
                        shining_id = setInterval(()=>{
                            if(shine){
                                shine = false;
                                $(`.gif`).attr("src",`static/3d_img/${response}_arrow.png`);
                            }
                            else{
                                shine = true;
                                $(`.gif`).attr("src",`static/3d_img/hold.png`);
                            }
                        },500);
                    }
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