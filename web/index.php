<?php

// CHANGE THIS TO YOUR jobs.sqlite3 file location
$dbfile = "/home/michael/src/jobbot/jobs.sqlite3";

function make_company($name){
	$name = preg_replace('/[^A-Za-z]/',' ',strtolower( $name ) );
	$name = preg_replace('/ \+/',' ',$name);
	$name = str_replace(' ','_',trim($name));
	return $name;
}


?><!DOCTYPE HTML>
<html>
<head>
<title>Michael Job Bot</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
html,body {
	max-width: 100%;
padding: 0;
margin: 0;
}
table {
width: 100%;
}
table,td,th {
  border: 1px solid black;
  border-collapse: collapse;
}
.desc {
	max-height: 100px;
	overflow: auto;
	font-size: smaller;
	color: rgb(75,75,75);
}
.handled,.applied {
text-align: center;
}
.rowignore {
	display: none;
}
.rownotapplied {
	display: none;
}
.rowcompanyhide {
	display: none;
}
select {
width: 100px;
}
</style>
<script src="jquery.min.js"></script>
</head>
<body>

<?php
$db = new SQLite3($dbfile);

$results = $db->querySingle('SELECT COUNT(*) FROM jobs');
$not_handled = $db->querySingle('SELECT COUNT(*) FROM jobs WHERE ignore=1');
$applied = $db->querySingle('SELECT COUNT(*) FROM jobs WHERE applied=1');
$companies_res = $db->query('SELECT DISTINCT company FROM jobs ORDER BY company');
$companies = array();
while($row = $companies_res->fetchArray(SQLITE3_ASSOC)){
	$companies[make_company($row['company'])] = $row['company'];
}

$companies = array_filter($companies);

print "<h1>Michael Job Bot</h1>";
print $results . " known jobs (" . $not_handled . " ignored, " . $applied . " applied)";

?>
<table><tr>
	<th>Ignore<br><input type="checkbox" id="ignoretoggle" checked></th>
	<th>Applied<br><input type="checkbox" id="appliedtoggle"></th>
	<th>Job<br><select id="companyfilter"><option value="---">All</option><?php
	foreach($companies as $id => $company) {
		print("<option value=\"$id\">$company</option>\n");
	}

?></select></th>
	<th>Date Found</th>
</tr>
<?php

$results = $db->query('SELECT * FROM jobs ORDER BY date_found DESC');
while($row = $results->fetchArray()){
	print("<tr class='jobrow " . ($row['ignore'] ? 'rowignore' : "" ) . "'>");
	print("<td class='handled'><input class='handledbox' data-id='" . $row['id'] . "' type='checkbox' " . ($row['ignore'] ? 'checked' : '') . "></td>");
	print("<td class='applied'><input class='appliedbox ' data-id='" . $row['id'] . "' type='checkbox' " . ($row['applied'] ? 'checked' : '') . "></td>");
	print("<td class='" . make_company($row['company']) . "'>" . $row['company'] . ": <a href='" . htmlentities($row['joblink']) . "' target='_blank'>" . $row['title'] . "</a>
<div class='desc'>" . htmlspecialchars($row['desc']) . "</div></td>");
	print("<td>" . date("Y-m-d",strtotime($row['date_found'])) . "</td>");
	print("</tr>\n");
}
print("</table>");

?>
<script>
jQuery('.handledbox').on('click',function(e){
	// e.target.checked
	jQuery.get('ajax.php',{
	'toggle_ignore': e.target.checked,
	'id': jQuery(e.target).data('id')
	});
});
jQuery('.appliedbox').on('click',function(e){
	// e.target.checked
	jQuery.get('ajax.php',{
	'toggle_applied': e.target.checked,
	'id': jQuery(e.target).data('id')
	});
});
jQuery('#ignoretoggle').on('click',function(e){
	if ( e.target.checked ) {
		jQuery('.handledbox:checked').closest('.jobrow').addClass('rowignore');
	} else {
		jQuery('.rowignore').removeClass('rowignore') 
	}
});

jQuery('#ignoretoggle').on('click',function(e){
	if ( e.target.checked ) {
		jQuery('.handledbox:checked').closest('tr').addClass('rowignore');
	} else {
		jQuery('.rowignore').removeClass('rowignore') 
	}
});

jQuery('#appliedtoggle').on('click',function(e){
	if ( e.target.checked ) {
		jQuery('.appliedbox').not(':checked').closest('tr').addClass('rownotapplied');
	} else {
		jQuery('.rownotapplied').removeClass('rownotapplied') 
	}
});

jQuery('#companyfilter').on('change',function(e){
	if ( e.target.value == '---' ){
		jQuery('.rowcompanyhide').removeClass('rowcompanyhide');
	} else {
		jQuery('.jobrow').addClass('rowcompanyhide');
		jQuery('.' + e.target.value).closest('.jobrow').removeClass('rowcompanyhide');
	}
});

jQuery('td.handled').on('click',function(e){
	jQuery(e.target).find('input:first').trigger('click');
});

jQuery('td.applied').on('click',function(e){
	jQuery(e.target).find('input:first').trigger('click');
});


</script>
</body>
</html>
