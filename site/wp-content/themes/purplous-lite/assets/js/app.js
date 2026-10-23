 $ = jQuery.noConflict();

 extendnav();
// Menu dropdown on hover
function extendnav() {
    jQuery('#primary-nav .dropdown').hover(function () {
        // Use show(), hide() instead of fade(), fadeOut().
        // Fade causes dropdown to wobble if mouse hover activity is faster..
        // Not a bug cause fade takes time to show() or hide() the element.
        // But show(), hide() does not take time to handle the same event
        $(this).children('.dropdown-menu').stop(true, true).show().addClass('slow fadeIn');
        $(this).toggleClass('open');
    }, function () {
        $(this).children('.dropdown-menu').stop(true, true).hide().removeClass('slow fadeIn');
        $(this).toggleClass('open');
    });
}

function responsiveIframe(){
var videoSelectors = [
  'iframe[src*="player.vimeo.com"]',
  'iframe[src*="youtube.com"]',
  'iframe[src*="youtube-nocookie.com"]',
  'iframe[src*="kickstarter.com"][src*="video.html"]',
  'iframe[src*="screenr.com"]',
  'iframe[src*="blip.tv"]',
  'iframe[src*="dailymotion.com"]',
  'iframe[src*="viddler.com"]',
  'iframe[src*="qik.com"]',
  'iframe[src*="revision3.com"]',
  'iframe[src*="hulu.com"]',
  'iframe[src*="funnyordie.com"]',
  'iframe[src*="flickr.com"]',
  'embed[src*="v.wordpress.com"]',
  'iframe[src*="videopress.com"]',
            'embed[src*="videopress.com"]'
  // add more selectors here
];
var allVideos = videoSelectors.join( ',' );
jQuery( allVideos ).wrap( '<span class="media-holder" />' );
}
// Responsive Iframes
  responsiveIframe();

  
// Top articlesslider for fullwidth layout
$('.fullwidth-layout .top-article').slick({
  infinite: true,
  autoplaySpeed: 7000,
  arrows: false,
  slidesToShow: 4,
  slidesToScroll: 4,
  responsive: [
      {
        breakpoint: 990,
        settings: {
          slidesToShow: 3,
          slidesToScroll: 3,
          infinite: true,
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 2
        }
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1
        }
      }
  ]
});


//for boxed layout
$('.boxed-layout .top-article').slick({
  infinite: true,
  autoplaySpeed: 7000,
  arrows: false,
  slidesToShow: 3,
  slidesToScroll: 3,
  responsive: [
      {
        breakpoint: 990,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 2,
          infinite: true,
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 2
        }
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1
        }
      }
  ]
});


// Post gallery slider

$('.post-gallery').slick({
  dots: false,
  infinite: true,
  speed: 500,
  autoplay: true,
  arrows: true,
});

//Related posts
// Top articlesslider
$('.sidebar-page .related-posts').slick({
  infinite: false,
  autoplaySpeed: 7000,
  arrows: true,
  slidesToShow: 2,
  slidesToScroll: 1,
  responsive: [
      {
        breakpoint: 990,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 1,
          infinite: true,
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        }
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        }
      }
  ]
});

$('.no-sidebar .related-posts').slick({
  infinite: false,
  autoplaySpeed: 7000,
  arrows: true,
  slidesToShow: 3,
  slidesToScroll: 2,
  responsive: [
      {
        breakpoint: 990,
        settings: {
          slidesToShow: 3,
          slidesToScroll: 2,
          infinite: true,
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 1,
        }
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        }
      }
  ]
});

// fit audio
jQuery('.post-audio-holder').each(function(){
  var fitvidheight = jQuery(this).parent().height();
  jQuery(this).find('iframe').addClass('fitiframe').css('height', fitvidheight);
});



