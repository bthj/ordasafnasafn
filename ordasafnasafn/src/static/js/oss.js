
$(document).bind("mobileinit", function(){
	$.mobile.page.prototype.options.addBackBtn = true;
	$.mobile.page.prototype.options.backBtnText = "Til baka";
});


$(function(){
	var oss = null;
	var wordBankDefaults = {
		"SearchHugtakasafn" : { "active" : true },
		"SearchIsmal" : { "active" : true },
		"SearchTos" : { "active" : false },
		"SearchBin" : { "active" : false },
		"SearchHafro" : { "active" : false },
		"SearchMalfar" : { "active" : false },
		"SearchRitmalaskra" : { "active" : false }
	};
	
	try {
		var isLocalStorage = ('localStorage' in window && window['localStorage'] !== null);
	} catch (e) {
		var isLocalStorage = false;
	}	

	if( isLocalStorage ) {
		if( localStorage["ordasafnasafn"] ) {
			oss = JSON.parse( localStorage["ordasafnasafn"] );
		}
		if( ! oss ) {
			oss = {};
		}
		$.each(wordBankDefaults, function(key, value){
			if( ! oss[key] ) oss[key] = value;
		});
		localStorage["ordasafnasafn"] = JSON.stringify( oss );
		
		// TODO:  update flip switches
	} else {
		oss = wordBankDefaults;
	}
	
	$.each( oss, function(wordbank, settings){
		var $wordbankSwitch = $("select[name="+wordbank+"]");
		if( settings.active ) {
			$wordbankSwitch[0].selectedIndex = 1;
		} else {
			$wordbankSwitch[0].selectedIndex = 0;
		}
	});
	
	
	function updateActiveInLocalStorage( ordasafn, isActive ) {
		if( isLocalStorage ) {
			oss[ordasafn].active = isActive;
			localStorage["ordasafnasafn"] = JSON.stringify( oss );
		}
	}
	
	
	function searchWordbank( $wordBank ) {
		var query = $("#query").val();
		if( query ) {
			$wordBank.find(".results").remove();
			$wordBank.find(".searching").remove();
			var liSearching = $('<li/>', {'class': 'searching'});
			var h4 = $('<h4/>').append('<em>Leita...</em>');
			liSearching.append(h4);
			$wordBank.append( liSearching ).listview("refresh");
			
			var ordasafn = $wordBank.attr("id");
			$.getJSON( '/search?ordasafn='+ordasafn+'&q='+query, function(data){  // TODO: error handling with $.ajax instead
				$wordBank.find(".searching").remove();
				var wordBankName = $wordBank.attr("data-wordbankname");
				
				if( data && data.length > 0) {
					$.each( data, function(idx, oneResultArray){
						var h4content = [];
						var textLegend = "";
						var litems = [];
						var itemCount = 0;
						var liResults = $('<li/>', {'class': 'results'});
						var h3 = $('<h3/>').attr('style', 'display:none;').append( wordBankName );
						liResults.append(h3);
						$.each( oneResultArray, function( index, oneEntry ){
							if( oneEntry.text ) {
								h4content.push( oneEntry.text );
							} else if( oneEntry.textlegend ) {
								textLegend = oneEntry.textlegend;
							}
							if( oneEntry.link ) {
								var litemParts = ['<li><a href="'+oneEntry.link+'" target="_blank">', '</a></li>'];
								if( oneEntry.html ) {
									litems.push( litemParts.join( oneEntry.html ) );
								} else {
									litems.push( litemParts.join( oneEntry.text ) );
								}
								itemCount++;
							} else if( oneEntry.text ) {
								if( oneEntry.html ) {
									litems.push( '<li>'+oneEntry.html+'</li>' );
								} else {
									litems.push( '<li>'+oneEntry.text+'</li>' );	
								}
								itemCount++;
							}
						});
						var h4 = $('<h4/>');
						if( textLegend ) h4.append( "[" + textLegend + "] " );
						h4.append( h4content.join( ', ' ) );
						var span = $('<span/>', {
							'class': 'ui-li-count',
							html: itemCount
						});
						liResults.append(h4).append(span);
						
						if( itemCount ) {
							var ul = $('<ul/>', {
								html: litems.join('')
							});
							liResults.append(ul);
						}
						$wordBank.append( liResults );
					});
				}
				$wordBank.listview("refresh");
			});			
		}
	}
	
	$("#search").submit(function(event){
		$("ul.wordbank").each(function(){
			var $wordBank = $(this);
			var isActive = $wordBank.find("select").val() == "on";
			if( isActive ) searchWordbank( $wordBank );
		});
		return false;
	});
	
	function updateWordbankPosition( $wordBank, isOn ) {
		if( isOn ) {
			// find next above is off, move above topmost one that is off
		} else {
			// find if any below is on, move beneath last one that is on
		}
	}

	$("#oss select").change(function(event){
		$currentSwitch = $(this);
		$wordBank = $currentSwitch.closest("ul");
		var ordasafn = $wordBank.attr("id");		
		if( $currentSwitch.val() == "on" ) {
			updateActiveInLocalStorage( ordasafn, true );
			searchWordbank( $wordBank );
			updateWordbankPosition( $wordBank, true );
		} else {
			$currentSwitch.closest("ul").find(".results").remove();
			updateActiveInLocalStorage( ordasafn, false );
			updateWordbankPosition( $wordBank, false );
		}
	});
	
	
});