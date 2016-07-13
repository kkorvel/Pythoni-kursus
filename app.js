function loadDoc() {
  var xhttp;
  if (window.XMLHttpRequest) {
    xhttp = new XMLHttpRequest();
    } else {
    xhttp = new ActiveXObject("robot.html");
  }
  xhttp.onreadystatechange = function() {
    if (xhttp.readyState == 4 && xhttp.status == 200) {
      document.getElementById("java").innerHTML = xhttp.responseText;
    }
  };
  xhttp.open("GET", "ajax_info.txt", true);
  xhttp.send();
}
function removeMobileOnclick() {
    if(isMobile()) {
        document.querySelector('.mobile-head-bar-left').onclick  = '';
    }
}

//working with phones when the touch start and the when the touch end 
window.addEventListener('load', removeMobileOnclick);
$('button').bind('touchstart', function(){
    $(this).addClass('button');
}).bind('touchend', function(){
    $(this).removeClass('button');
});


//calling the function of the battery status
setInterval(function(){ 
    $.getJSON('/batterystatus', function(data) {
        $("#batterystats").text(data.power/1000000 + " Watts ");
        $("#voltage").text(data.voltage/1000000 + " Voltage ");
        $("#circleleft").toggleClass("activated", data.enemy_left == 1);
        $("#circleright").toggleClass("activated", data.enemy_right == 1);
        $("#capacity").text(data.capacity + "% power");
        $("#charge").css("width", data.capacity + "%");
        // variable 'data' does not exist after this
    });
}, 1000); 
    
//disable the text selection
$.fn.extend({
    disableSelection: function() {
        this.each(function() {
            this.onselectstart = function() {
                return false;
            };
            this.unselectable = "on";
            $(this).css('-moz-user-select', 'none');
            $(this).css('-webkit-user-select', 'none');
        });
        return this;
    }
});

//for computer controls 
$("html").keydown(function(e) {
    e.preventDefault();
    switch (e.keyCode) {
        case 37:
            $.get('/left');
            //console.info("Pressed Left");
            break
        case 39:
	$.get("/right");
            //console.info("Pressed Right");
            break;
        case 38:
            $.get("/go");
            //console.info("Pressed Go");
            break;
         case 40:
            $.get("/back");
        default:
        		$("#msg").html("Pressed back button");
            //console.info("User Pressed back button:", e.keyCode);
    }
    return false;
});

$("html").keyup(function(e) {
    $.get("/stop");
    e.preventDefault(); // Prevent page from scrolling
    return false;
});

//calling the network interfaces
window.networkUpdates = setInterval(function(){ 
    $.getJSON('/api/wireless', function(data) {
        $("#networks").empty();
        $.each(data, function(i, e) {
        //console.info("appending:", e); View the networks interfaces in the console
        $("#networks").append("<option>" + e.ssid + "</option>");
        });
    });
}, 3000); 
