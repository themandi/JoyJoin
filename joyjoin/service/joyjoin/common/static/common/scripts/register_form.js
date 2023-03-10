var loginFocus = false;
var nameFocus = false;
var emailFocus = false;
var passwordFocus = false;
var password2Focus = false;
var ageFocus = false;
var rulesFocus = false;

var loginCorrect = false;
var nameCorrect = false;
var emailCorrect = false;
var passwordCorrect = false;
var password2Correct = false;
var ageCorrect = false;
var rulesCorrect = false;

$(document).ready(function(){

    // login focusin focusout
    $("#rpf_login").on("input focusin", function() {
        loginFocus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_login").css("display", "none");
        check_login();
    });

    $("#rpf_login").on("focusout", function() {
        loginFocus = false;
    });
    
    // name focusin focusout
    $("#rpf_name").on("input focusin", function() {
        nameFocus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_name").css("display", "none");
        check_name();
    });

    $("#rpf_name").on("focusout", function() {
        nameFocus = false;
    });

    // email focusin focusout
    $("#rpf_email").on("input focusin", function() {
        emailFocus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_email").css("display", "none");
        check_email();
    });

    $("#rpf_email").on("focusout", function() {
        emailFocus = false;
    });

    // password focusin focusout
    $("#rpf_password").on("input focusin", function() {
        passwordFocus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_password").css("display", "none");
        check_password();
    });

    $("#rpf_password").on("focusout", function() {
        passwordFocus = false;
    });

    // password2 focusin focusout
    $("#rpf_password2").on("input focusin", function() {
        password2Focus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_password2").css("display", "none");
        check_password2();
    });

    $("#rpf_password2").on("focusout", function() {
        password2Focus = false;
    });

    // birth_date focusin focusout
    $("#rpf_birth_date").on("input focusin", function() {
        ageFocus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_birth_date").css("display", "none");
        check_birth_date();
    });

    $("#rpf_birth_date").on("focusout", function() {
        ageFocus = false;
    });

    // rules focusin focusout
    $("#rpf_rules").on("input", function() {
        rulesFocus = true;
        $(".warning label").hide();
        $(".warning hr").hide();
        $("#warning_panel_rpf_rules").css("display", "none");
        check_rules();
    });

    $("#rpf_rules").on("focusout", function() {
        rulesFocus = false;
    });

    $("input").on("focusout", function() {
        $("#warning_panel_" + this.id ).css("display", "none");
    });
})

function form_submit() {
    var correct = true;

    if (!loginCorrect) {
        check_login();
        correct = false;
    }
    if (!nameCorrect) {
        check_name();
        correct = false;
    }
    if (!emailCorrect) {
        check_email();
        correct = false;
    }
    if (!passwordCorrect) {
        check_password();
        correct = false;
    }
    if (!password2Correct) {
        check_password2();
        correct = false;
    }
    if (!ageCorrect) {
        check_birth_date();
        correct = false;
    }
    if (!rulesCorrect) {
        check_rules();
        correct = false;
    }
    
    if (correct) {
        $("#register_panel_form").submit();
    }
}

function check_login() {
    loginCorect = false;
    var login = $("#rpf_login").val();
    var correct = true;
    var letter = /[a-z]/
    var bad_characters = /[^a-z0-9_]/

    if (!login) {
        $("#rpf_login_empty").show();
        correct = false;
    }
    else {
        if (login.length < 3 || login.length > 20) {
            if (!correct) $("#rpf_login_bad_length_hr").show();
            $("#rpf_login_bad_length").show();
            correct = false;
        }

        if (!login.charAt(0).match(letter)) {
            if (!correct) $("#rpf_login_first_letter_hr").show();
            $("#rpf_login_first_letter").show();
            correct = false;
        }

        if (login.match(bad_characters)) {
            if (!correct) $("#rpf_login_bad_character_hr").show();
            $("#rpf_login_bad_character").show();
            correct = false;
        }

    }

    if (!correct) {
        // login nieprawidłowy
        $("#rpf_login").removeClass("correct");
        $("#rpf_login").addClass("incorrect");
        if (loginFocus) {
            $("#warning_panel_rpf_login").css("display", "inline-block");
        }
    }
    else {
        // sprawdzenie czy login jest wolny
        $("#rpf_login_request_input").val(login);
            var form = $('#rpf_login_request');
            
            $.ajax({
                type: form.attr('method'),
                url: form.attr('action'),
                data: form.serialize(),
                success: function(data) {  
                    if (data=="false") {
                        // login zajęty
                        $("#rpf_login_used").show();
                        $("#rpf_login").removeClass("correct");
                        $("#rpf_login").addClass("incorrect");
                        
                        if (loginFocus) {
                            $("#warning_panel_rpf_login").css("display", "inline-block");
                        }
                    }
                    else {
                        // login wolny
                        $("#rpf_login").removeClass("incorrect");
                        $("#rpf_login").addClass("correct");
                        loginCorrect = true;
                    }
                },
                error: function(data) {        
                }
            });
    }  
}

function check_name() {
    nameCorrect = false;
    var name = $("#rpf_name").val();
    var correct = true;
    var letter = /[a-z]/
    var bad_characters = /[^a-zA-z ąęćżźńółśĄĘĆŻŹŃÓŁŚ]/

    if (!name) {
        $("#rpf_name_empty").show();
        correct = false;
    }
    else {
        if (name.length < 3 || name.length > 63) {
            if (!correct) $("#rpf_name_bad_length_hr").show();
            $("#rpf_name_bad_length").show();
            correct = false;
        }

        if (name.match(bad_characters)) {
            if (!correct) $("#rpf_name_bad_character_hr").show();
            $("#rpf_name_bad_character").show();
            correct = false;
        }
    }

    nameCorrect = correct;
    if (!correct) {
        $("#rpf_name").removeClass("correct");
        $("#rpf_name").addClass("incorrect");
        if (nameFocus) {
            $("#warning_panel_rpf_name").css("display", "inline-block");
        }
    }
    else {
        $("#rpf_name").removeClass("incorrect");
        $("#rpf_name").addClass("correct");
    }
}

function check_email() {
    emailCorrect = false;
    var email = $("#rpf_email").val();
    var correct = true;
    var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    
    if (!email) {
        $("#rpf_email_empty").show();
        correct = false;
    }
    else {
        if (!regex.test(email)) {
            $("#rpf_email_bad").show();
            correct = false;
        }
    }
    emailCorrect = correct;
    if (!correct) {
        $("#rpf_email").removeClass("correct");
        $("#rpf_email").addClass("incorrect");
        if (emailFocus) {
            $("#warning_panel_rpf_email").css("display", "inline-block");
        }
    }
    else {
        $("#rpf_email").removeClass("incorrect");
        $("#rpf_email").addClass("correct");
    }
}

function check_password() {
    passwordCorrect = false;
    var password = $("#rpf_password").val();
    var correct = true;
    var good_characters = /[^0-9]/

    if (!password) {
        $("#rpf_password_empty").show();
        correct = false;
    }
    else {
        if (password.length < 8) {
            if (!correct) $("#rpf_password_short_hr").show();
            $("#rpf_password_short").show();
            correct = false;
        }

        if (!password.match(good_characters)) {
            if (!correct) $("#rpf_password_numeric_hr").show();
            $("#rpf_password_numeric").show();
            correct = false;
        }
    }

    if (!correct) {
        // hasło niepoprawne
        $("#rpf_password").removeClass("correct");
        $("#rpf_password").addClass("incorrect");
        $("#rpf_password2").prop("disabled", true);
        $("#rpf_password2").removeClass("correct");
        $("#rpf_password2").removeClass("incorrect");
        if (passwordFocus) {
            $("#warning_panel_rpf_password").css("display", "inline-block");
        }
    }
    else {
        // sprawdzenie czy hasło nie jest zbyt proste
        $("#rpf_password_request_input").val(password);
        var form = $('#rpf_password_request');

        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(data) {  
                if (data=="false") {
                    // zbyt proste hasło
                    $("#rpf_password_too_common").show();
                    $("#rpf_password").removeClass("correct");
                    $("#rpf_password").addClass("incorrect");
                    $("#rpf_password2").prop("disabled", true);
                    $("#rpf_password2").removeClass("correct");
                    $("#rpf_password2").removeClass("incorrect");
                    if (passwordFocus) {
                        $("#warning_panel_rpf_password").css("display", "inline-block");
                    }
                }
                else {
                    // dobre hasło
                    $("#rpf_password2").prop("disabled", false);
                    $("#rpf_password").removeClass("incorrect");
                    $("#rpf_password").addClass("correct");
                    passwordCorrect = true;
                    check_password2();
                }
            },
            error: function(data) {        
            }
        });
    }
    
}

function check_password2() {
    if (!passwordCorrect) {
        return;
    }
    password2Correct = false;
    var password1 = $("#rpf_password").val();
    var password2 = $("#rpf_password2").val();
    var correct = true;

    if (!password2) {
        $("#rpf_password2_empty").show();
        correct = false;
    }
    else {
        if (password2 != password1) {
            $("#rpf_password2_different").show();
            correct = false;
        }
    }

    password2Correct = correct;
    if (!correct) {
        $("#rpf_password2").removeClass("correct");
        $("#rpf_password2").addClass("incorrect");
        if (password2Focus) {
            $("#warning_panel_rpf_password2").css("display", "inline-block");
        }
    }
    else {
        $("#rpf_password2").removeClass("incorrect");
        $("#rpf_password2").addClass("correct");
    }    
}

function check_birth_date() {
    ageCorrect = false;
    var birth_date = $("#rpf_birth_date").val();
    var date = new Date(birth_date);
    var age = Date.now() - date;
    var correct = true;

    if (!birth_date) {
        $("#rpf_birth_date_empty").show();
        correct = false;
    }

    if (!correct) {
        // data niepoprawna
        $("#rpf_birth_date").removeClass("correct");
        $("#rpf_birth_date").addClass("incorrect");
        if (ageFocus) {
            $("#warning_panel_rpf_birth_date").css("display", "inline-block");
        }
    }
    else {
        // sprawdzenie czy wiek jest dopowiedni (12-120 lat)
        var year = date.getFullYear();
        var month = date.getMonth()+1;
        var day = date.getDate();
        if (date.getMonth() + 1< 10) {
            month = "0"+month.toString();
        }
        if (date.getDate() < 10) {
            day = "0"+day.toString();
        }
        var final_date = year.toString()+"-"+month.toString()+"-"+day.toString();
        $("#rpf_date_request_input").val(final_date);
        var form = $('#rpf_date_request');

        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(data) {  
                if (data=="false") {
                    // zły wiek
                    $("#rpf_birth_date_age").show();
                    $("#rpf_birth_date").removeClass("correct");
                    $("#rpf_birth_date").addClass("incorrect");
                    if (ageFocus) {
                        $("#warning_panel_rpf_birth_date").css("display", "inline-block");
                    }
                }
                else {
                    // dobry wiek
                    $("#rpf_birth_date").removeClass("incorrect");
                    $("#rpf_birth_date").addClass("correct");
                    ageCorrect = true;
                }
            },
            error: function(data) {   
            }
        });
    }
}

function check_rules() {
    rulesCorrect = false;
    var correct = true;
    if(!$('#rpf_rules')[0].checked) {
        $("#rpf_rules_empty").show();
        correct = false;
    }

    rulesCorrect = correct;
    if (!correct) {
        $("#rpf_rules").removeClass("correct");
        $("#rpf_rules").addClass("incorrect");
        $("#accept_rules").css("text-decoration", "underline");
        $("#accept_rules").css("color", "red");
        if (rulesFocus) {
            $("#warning_panel_rpf_rules").css("display", "inline-block");
        }
    }
    else {
        $("#accept_rules").css("text-decoration", "none");
        $("#accept_rules").css("color", "green");
        $("#rpf_rules").removeClass("incorrect");
        $("#rpf_rules").addClass("correct");
    }
}
