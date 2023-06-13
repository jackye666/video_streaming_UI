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

    function handle_gif(img_url){
        // console.log(img_url);
        // let complete = document.getElementById("gif").complete;
        // while(!complete){

        // }
        // console.log("complete!",$("#gif").attr("src"))
        $("#gif").attr("src",img_url);
        // console.log((document.getElementById("gif").complete));
    }
    setInterval(()=>{
        $.ajax({
            url:"/move_prediction",
            method:"GET",
            success: function(response){
                console.log(response);
                var img_url = `static/gif/${response}.gif`;
                // $("#gif").attr("src",img_url);
                $("#gif").on("load",handle_gif(img_url));
                // $("#gif").off("load.myNamespace")
            }
        })
    },3000)


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