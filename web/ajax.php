<?php

// CHANGE THIS TO YOUR jobs.sqlite3 file location
$dbfile = "/home/michael/src/jobbot/jobs.sqlite3";

header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");


// Handle slack response
if ( array_key_exists('payload',$_REQUEST)) {

	$payload = json_decode($_REQUEST['payload'],TRUE);

	$db = new SQLite3($dbfile);

	foreach($payload['actions'] as $action){
		$job_id = str_replace('job-','',$action['action_id']);
		$value = $action['selected_option']['value'];

		if ( $value  == '1' ) {
			$q = 'UPDATE jobs set ignore=1 WHERE id=' . SQLite3::escapeString((int)$job_id);
			$results = $db->query($q);
			$res_msg = "The job will not be shown any more.";
			$payload['message']['blocks'][0]['text']['text'] = preg_replace("|^.*JobBot!|","🙅JobBot!", $payload['message']['blocks'][0]['text']['text']);
		} else if ( $value == '0' ) {
			$q = 'UPDATE jobs set ignore=0 WHERE id=' . SQLite3::escapeString((int)$job_id);
			$results = $db->query($q);
			$res_msg = "The job will be saved for later.";
			$payload['message']['blocks'][0]['text']['text'] = preg_replace("|^.*JobBot!|","✅JobBot!", $payload['message']['blocks'][0]['text']['text']);
		} else {
			$res_msg = "I don't know what to do.";
		}
	}

	/*
	Post slack response
	POST https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
	Content-type: application/json
	{
		"text": "Oh hey, this is a nifty ephemeral message response!"
	}
	 */

	//The data you want to send via POST
	$fields = [
		'text' =>  $res_msg
	];

	$fields = [
		"blocks" => [
	[
		"type" => "header",
			"text"=>[
			"type"=>"plain_text",
				"text"=>"New header here"
			]]
	,
	[
		"type"=>"section",
			"text"=>[
			"type"=>"mrkdwn",
				"text"=>"ASDFASDFQWERQWEASDF"

			]]
		]
	];

	$fields = $payload['message'];

	//open connection
	$url = $payload['response_url'];
	$ch = curl_init();

	//set the url, number of POST vars, POST data
	curl_setopt($ch,CURLOPT_URL, $url);
	curl_setopt($ch,CURLOPT_POST, true);
	curl_setopt( $ch, CURLOPT_HTTPHEADER, array('Content-Type:application/json'));
	curl_setopt($ch,CURLOPT_POSTFIELDS, json_encode($fields));

	//So that curl_exec returns the contents of the cURL; rather than echoing it
	curl_setopt($ch,CURLOPT_RETURNTRANSFER, true);

	$result = curl_exec($ch);
	curl_close($ch);
	print "OK";
} else if (isset($_GET['toggle_ignore']) && isset($_GET['id'])) {

	$dbfile = "/home/michael/src/jobbot/jobs.sqlite3";
	$db = new SQLite3($dbfile);

	if ( $_GET['toggle_ignore'] == 'true' ) {
		$q = 'UPDATE jobs set ignore=1 WHERE id=' . SQLite3::escapeString((int)$_GET['id']);
		$results = $db->query($q);
	} else {
		$q = 'UPDATE jobs set ignore=0 WHERE id=' . SQLite3::escapeString((int)$_GET['id']);
		$results = $db->query($q);
	}
	print "OK";
} else if (isset($_GET['toggle_applied']) && isset($_GET['id'])) {

	$dbfile = "/home/michael/src/jobbot/jobs.sqlite3";
	$db = new SQLite3($dbfile);

	if ( $_GET['toggle_applied'] == 'true' ) {
		$q = 'UPDATE jobs set applied=1 WHERE id=' . SQLite3::escapeString((int)$_GET['id']);
		$results = $db->query($q);
	} else {
		$q = 'UPDATE jobs set applied=0 WHERE id=' . SQLite3::escapeString((int)$_GET['id']);
		$results = $db->query($q);
	}
	print "OK";
} 
