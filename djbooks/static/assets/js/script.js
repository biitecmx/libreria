(function ($) {
    "use strict";

    /*************************
     tap to top js start
     *************************/

    $(window).on('scroll', function () {
        if ($(this).scrollTop() > 500) {
            $('.tap-top').fadeIn();
        } else {
            $('.tap-top').fadeOut();
        }
    });
    $('.tap-top').on('click', function () {
        $("html, body").animate({
            scrollTop: 0
        }, 600);
        return false;
    });

    /*************************
     tap to top js end
     *************************/

    /*************************
        slider js start
     *************************/
    $('.slide-center-3').slick({
        centerMode: true,
        centerPadding: '200px',
        slidesToShow: 2,
        dots: true,
        responsive: [
            {
                breakpoint: 1199,
                settings: {
                    centerPadding: '150px'
                }
            },
            {
                breakpoint: 768,
                settings: {
                    arrows: false,
                    centerMode: true,
                    centerPadding: '50px',
                    slidesToShow: 1
                }
            }
        ]
    });
    $('.slide-1').slick({
        dots: true,
        infinite: false,
        speed: 300,
        slidesToShow: 1,
        slidesToScroll: 1,
    });

  
})(jQuery);
