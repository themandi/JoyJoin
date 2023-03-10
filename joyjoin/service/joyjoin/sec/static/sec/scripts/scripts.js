// Nadanie koloru #navbar
$(document).ready(function() {
    navbarColor();
});

$(window).on('scroll', function() {
	navbarColor();
});

function navbarColor() {
	if ($(window).scrollTop()) {
		$("#navbar").addClass("navbar-color");
	}
	else {
		$("#navbar").removeClass("navbar-color");
	}
}
