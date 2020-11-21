var menu_as_bar = false;
var barClasses = ["w3-mobile","w3-bar","w3-collapse","w3-hide-small","w3-hide-medium"];
var sideClasses = ["w3-mobile","w3-sidebar","w3-bar-block","w3-collapse","w3-right","w3-card","w3-animate-right","w3-secondary-color","menu_width","nav-sidebar-extra"];

function set_menu_type(is_bar){
    menu_as_bar = is_bar;
}

function swapClasses(target,addOrRemove,classList){
  // add or remove classes in target with values from classList
  for(var i = 0; i<classList.length; i++){
    if(addOrRemove.toLowerCase() == 'add'){
     $(target).addClass(classList[i]);
    } else {
      $(target).removeClass(classList[i]);
    }
  }
}

function set_menu_style(){
  // this is called when screen size changes
  // but only when the menu bar is specified
  var w = document.body.offsetWidth;
  
  swapClasses('#primary-nav', 'remove', barClasses);
  swapClasses('#primary-nav', 'add', sideClasses);
  swapClasses('#sg-content', 'add', ['menu_space']);
  swapClasses('#sg-identity', 'add', ['menu_space']);
  show_hamburger();
  $('#primary-nav').hide();

  if(w >= 993 ){
    if (menu_as_bar){
      swapClasses('#primary-nav', 'remove', sideClasses);
      swapClasses('#primary-nav', 'add', barClasses);
      swapClasses('#sg-content', 'remove', ['menu_space']);
      swapClasses('#sg-identity', 'remove', ['menu_space']);
      $('#primary-nav').show();
    } 
  } 
}

function show_hamburger(){
    $('#hamburger').show();
  }
  
function hide_hamburger(){
    $('#hamburger').hide();
  }
  
function primary_nav_toggle() {
    $('#primary-nav').toggle();
  }
  
$(window).resize(function(){set_menu_style();});
$(document).ready(function(){set_menu_style();});
