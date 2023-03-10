// Ustawienia początkowe
var rightMenuStart = 0;
var rightMenuPosition = 0;
var loginWindowVisible = false;
var accountWindowVisible = false;
var registerWindowVisible = false;
var semafor = false;
var newPosts = '';
var waitingForPosts = false;

$(document).ready(function() {
    scrolling();
    set_mobile_menu();
    hide_see_more_buttons()
    loadPosts();
});

$(window).on('scroll', function() {
	scrolling();
});

$(window).on('resize', function() {
	rightMenuStart = $('#banner').offset().top - 80;
    rightMenuPosition = $('#right-menu').offset().top - $('#banner').offset().top + 80;
    scrolling();
});

function scrolling() {
    leftMenu();
    rightMenu();
    upShow();
    displayPosts();
}

// Ustawienie contentu #mobile-menu
function set_mobile_menu() {
    var left_menu = document.getElementById("left-menu").innerHTML;
    $('#mobile_menu').append(left_menu);
    
    var options = document.getElementById("available-options").childNodes;
    var text = "";
    
    var i = 0;
    for (i = 0; i < options.length; i++) {
        if (options[i].innerHTML != undefined) {
            text += '<li>' + options[i].innerHTML + '<hr></li>';
        }
    }
    
    var register_button = '';
    if (document.getElementById("register") != null) {
        register_button = '<li class="mobile_buttons"><a onclick="show_register()">Zarejestruj</a><hr></li>';
    }
    
    var login_button = '';
    if (document.getElementById("login") != null) { 
        login_button = '<li class="mobile_buttons"><a onclick="show_login()">Zaloguj</a><hr></li>';
    }
    
    $('#mobile_menu').append('<ul id="mobile_options">' + text + register_button + login_button + '</ul>');
    
    $('#mobile_menu').append('<div id="mobile_footer"></div>');
    $('#footer').clone().appendTo($('#mobile_footer'));
}

// Pojawienie się #login-window
function show_login() {
    $('#dark-screen').fadeIn();
	$('#login-window').fadeIn();
}

function hide_see_more_buttons() {
    var posts = document.getElementsByClassName('post_text');
    var see_more = document.getElementsByClassName('see-more');
    
    for (var i = 0; i < posts.length; i++) {
        if (posts[i].offsetHeight < 500) {
            see_more[i].innerHTML = "";
        }
    }
}

// Pojawienie się #login-window
$(document).on('click', '#login', function(event){
	show_login();
});

// Pojawienie się #account-window
$(document).on('click', '#account', function(event){
	if (!accountWindowVisible) {
		$('#account-window').fadeIn('fast');
		accountWindowVisible = true;
	}
	else {
		$('#account-window').fadeOut('fast');
		accountWindowVisible = false;
	}
});

// Pojawienie się #dark-screen i #register-window
function show_register() {
    $('#dark-screen').fadeIn();
	$('#register-window').fadeIn();
}

// Pojawienie się #dark-screen i #register-window
$(document).on('click', '#register', function(event){
	show_register();
});

// Zamkniecie #dark-screen i #register-window
function closeRegistrationWindow() {
	$('#dark-screen').fadeOut();
	$('#register-window').fadeOut();
    $('#login-window').fadeOut();
}

// Zamkniecie #dark-screen i #register-window po kliknieciu na #dark-screen
$(document).on('click', '#dark-screen', function(event){
	closeRegistrationWindow();
});

// Zamkniecie #dark-screen i #register-window po kliknieciu na #register-exit
$(document).on('click', '#register-exit', function(event){
	closeRegistrationWindow();
});

// Zamknięcie #dark-screen i #register-window przez nacisniecie klawisza ESC
//https://stackoverflow.com/questions/3369593/how-to-detect-escape-key-press-with-pure-js-or-jquery
document.onkeydown = function(evt) {
    evt = evt || window.event;
    var isEscape = false;
    if ('key' in evt) {
        isEscape = (evt.key === 'Escape' || evt.key === 'Esc');
    } else {
        isEscape = (evt.keyCode === 27);
    }
    if (isEscape) {
        closeRegistrationWindow();
    }
};

// Zaczepienie #left-menu
function leftMenu() {
	if ($(window).scrollTop() >= $("#site").offset().top - 70) {
		$('#left-menu').addClass('fixed');
	}
	else {
		$('#left-menu').removeClass('fixed');
	}
}

// Zaczepienie #right-menu
function rightMenu() {
    if (rightMenuStart == 0) { 
        rightMenuStart = $('#banner').offset().top - 80;
        rightMenuPosition = $('#right-menu').offset().top - $('#banner').offset().top + 80;
    }
    if ($(window).scrollTop() >= rightMenuStart) {
		$('#right-menu').css('position', 'fixed');
		$('#right-menu').css("top", rightMenuPosition);
	}
	else {
		$('#right-menu').css('position', 'static');
	}
}

function upShow() {
	if ($(window).scrollTop() >= 2000) {
		$('#up').fadeIn('slow');
	}
	else {
		$('#up').fadeOut('slow');
	}
}

// Powrót na początek strony
$(document).on('click', '#up', function(event){
	window.scroll({top: 0,  behavior: 'smooth'});
});

// Infinite scrolling
function loadPosts() {
    var form = $('#display_new_posts');
    if (form.attr('action') == undefined) return;

    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        async: true,
        success: function(data) {
            newPosts = data;
            if (newPosts == '\n') newPosts = '';
            
            if (waitingForPosts) displayPosts();
        },
        error: function(data) {
        },
        complete: function(data) {
        }
    });
}

function displayPosts() {
    if (newPosts == '') waitingForPosts = true;
    else waitingForPosts = false;
    
    if (newPosts != '' && $(window).scrollTop() >= $(document).height() - $(window).height() - 50 && semafor == false) {
        semafor = true;
        $('#content').append(newPosts);
        newPosts = '';
        hide_see_more_buttons();
        loadPosts();
        semafor = false;
    }
}

// Funkcja do wysyłania like/dislike
function like(type, id) {
    var form = $('#'+ type +'_form_' + id);

    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function(data) {
            if (data=="") {
                show_login();
            }
            else {
                var part = data.split("<br>")
                document.getElementById("like_button_"+id).innerHTML = part[0];
                document.getElementById("dislike_button_"+id).innerHTML = part[1];
            }
        },
        error: function(data) {
        }
    });
}

// Funkcja do wysyłania like/dislike do komentarzy
function commentLike(type, id) {
    var form = $('#comm'+ id +'form_' + type);

    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function(data) {
            if (data=="") {
                show_login();
            }
            else {
                var part = data.split("<br>")
                document.getElementById("comm_like_button_"+id).innerHTML = part[0];
                document.getElementById("comm_dislike_button_"+id).innerHTML = part[1];
            }
        },
        error: function(data) {
        }
    });
}

// Funkcja do wyświetlenia kontaktu
function showcontact()
{
    var x = document.getElementsByClassName("kontakt");
    
    if(x[0].style.display == "none" || x[0].style.display == "") 
    {
        x[0].style.display = "block";
        x[1].style.display = "block";
    } 
    else 
    {
        x[0].style.display = "none";
        x[1].style.display = "none";
    }
}

// Funkcja do zmiany wartości licznika suwaka w preferences.html
function changeCounter(tag_name) {
    document.getElementById("counter_"+tag_name).innerHTML = document.getElementById("range_"+tag_name).value;
}

//Funckja do resetowania punktacji do wartości domyślnej
function resetCounter(tag_name, value) {
    event.preventDefault();
    document.getElementById("range_"+tag_name).value = value;
    document.getElementById("counter_"+tag_name).innerHTML = value;
}

function show_mobile_menu() {
    var x = document.getElementById("mobile_menu");
    if(!x.classList.contains("visible")) 
    {
        $("#mobile_menu").addClass("visible");
    } 
    else 
    {
        $("#mobile_menu").removeClass("visible");
    }
}

function show_full_post(post_id) {
    event.preventDefault();
    
    if (document.getElementById('post_text_'+post_id).classList.contains('full')) {
        var x = 500-document.getElementById('post_text_'+post_id).offsetHeight;
        window.scrollBy({top: x});
        $('#post_text_'+post_id).removeClass('full');
        document.getElementById('see_more_'+post_id).innerHTML = 'Zobacz więcej<i class="icon-down-dir-2"></i>';
        
    }
    else {
        $('#post_text_'+post_id).addClass('full');
        document.getElementById('see_more_'+post_id).innerHTML = 'Zobacz mniej<i class="icon-up-dir-1"></i>';
    }
}
