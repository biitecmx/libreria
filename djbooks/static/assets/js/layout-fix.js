    $(window).on('scroll', function () {
        if ($(this).scrollTop() > 400) {
           $("header").addClass("fixed");
        } else {
            $("header").removeClass("fixed");
        }
    });

