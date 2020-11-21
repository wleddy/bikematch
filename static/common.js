/* common.js for app */

// for navigation buttons
function w3_open(id_name) {
    document.getElementById(id_name).style.display = "block";
}
function w3_close(id_name) {
    document.getElementById(id_name).style.display = "none";
}
function w3_hide(id_name) {
    document.getElementById(id_name).style.visibility = "hidden";
}
function w3_show(id_name) {
    document.getElementById(id_name).style.visibility = "visible";
}

function confirmRecordDelete(){
	return confirm("Are you sure you want to delete this record?");
}

function updateImage(imageSource,imageID) {
	$(imageID).attr("src",imageSource);
}

function editFromList(editFormURL) {
	setModal('dialog',true);
	$('#modal-form-contain').show();
	$('#modal-form').show();
	$('#modal-form').load(editFormURL,function(data){modalFormSuccess(data);})
	}

function modalFormSuccess(data){
	// return true if the update was successful
	// also return true if the update failed for a reason
	// other than a validation error
	var result = true;
	if (data.toLowerCase() == "success"){
		result = true;
	}
	else if (data.substr(0,9).toLowerCase() == 'failure: '){
		cancelModalForm();
		// display an error message
		alert(data.substr(9)) 
		result = true;
	} else { result = false; }
	if(result == true){ cancelModalForm(); }
	return result;
}

function submitModalToModalForm(formID, postingURL, successTarget, successURL,responseURL){
    /* Just like submitModalForm but doesn't close the modal form div on success */
	$("#modal-form").load(postingURL,formToJson(formID),function(data){
		if (data.toLowerCase() == 'success'){
			$("#"+successTarget).load(successURL);
            $("#modal-form").load(responseURL); // a new dialog after success
		} else {
			// there were errors, so the form will redisplay
		}
	}
	,"html");
}

function submitModalForm(formID, postingURL, successTarget, successURL){
	$("#modal-form").load(postingURL,formToJson(formID),function(data){
		if (modalFormSuccess(data)){
            if(successTarget == ''){
                // load a fresh page
                document.location=successURL;
            } else {
			    $("#"+successTarget).load(successURL);
            }
		} else {
			// there were errors, so the form will redisplay
		}
	}
	,"html");
}

function formToJson(formID){
	var raw = $("#"+formID).serializeArray();
	var obj = {};
	jQuery.each( raw, function( i, field ) { 
		if (obj[field.name] !== undefined) {
			if (!obj[field.name].push) {
				obj[field.name] = [obj[field.name]];
			}
			obj[field.name].push(field.value || '');
		} else {
			obj[field.name] = field.value || '';
		}
		
	});
	return obj;
}

function deleteFromList(deleteActionURL, successTarget){
	if (confirmRecordDelete()) {
		$.get(deleteActionURL, function(data){
		if(data == "success"){
			$("#"+successTarget).text('').hide();
		} else {
			alert(data)
		}
	})
	}
}

function cancelModalForm(){
	setModal("dialog",false);
	$("#modal-form").text("")
	$("#modal-form, #modal-form-contain").hide();
}

// Paint the screen with a div to simulate a modal dialog
function setModal(objectID,modalState) {
	var objectID = "#"+objectID;
	var docHeight = $(document).height()+"px";
	var docWidth = $(document).width()+"px";
	$(objectID).css("position","absolute").css("top","0").css("left","0");
	if(modalState) {
		// display the div
		$(objectID).css("height",docHeight).css("width",docWidth).show();
	}
	else {
		//hide the div
		docHeight = "1px";
		docWidth = "1px";
		$(objectID).css("height",docHeight).css("width",docWidth).hide();
	}
}

function getDateString(d) {
	// format the LOCAL time string into the ISO formatted string that the db expects
    var d = d || new Date();
    //var n = d.toISOString(); // toISOString always returns UTC time, not ISO formatted local time
	var dateString = (d.getFullYear() + "-");
	dateString += ("0" + (d.getMonth()+1)).substr(-2)+"-"
	dateString += ("0" + d.getDate()).substr(-2)
    return dateString;
	//$("#eventDate").val(dateString);
}


/* handle the search in most table list templates */

function toggle_table_search(table_id){
    /*
    show the search table and move it into position below the input field
    */
    var table = document.getElementById(table_id);
    
    if (table.style.display != 'none' && table.style.display != ''){ 
        table.style.display = 'none';
        table.style.position = 'static';
    }
    else
    {
        table.style.display = 'block';
        table.style.position = 'absolute'
    }
}


function reset_table_search(table_id){
    // ensure that all rows of the search table are visible
    var table = document.getElementById(table_id);
    var tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++) {
        tr[i].style.display = "";
    }
}

function table_search(input_field_id,table_id,column_num=0) {
  var input, filter, table, tr, td, i;
  input = document.getElementById(input_field_id);
  filter = input.value.toUpperCase();
  table = document.getElementById(table_id);
  
  // reset this display if no text
  if (filter.length == 0){reset_table_search(table_id);}
  
  tr = table.getElementsByTagName("tr");
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[column_num];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}