
 $('.menu-header-search a').on('click', function(e) {
    e.preventDefault();
    $('#header-search-wrap').toggleClass('show');
    $('#header-search-wrap').addClass('animated fadeInDown');
    $('#header-search-wrap').find('input[type="search"]').focus();
 });

  $('#header-search-wrap .close').on('click', function(e) {
    e.preventDefault();
    $('#header-search-wrap').removeClass('show');
  });