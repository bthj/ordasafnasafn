
$(document).bind("mobileinit", function(){
	$.mobile.page.prototype.options.addBackBtn = true;
	$.mobile.page.prototype.options.backBtnText = "Til baka";
});

var addthis_config = {
	services_exclude : "print",
	data_track_clickback: false
}

$(function(){
	var oss = null;
	var ossDefaults = {
		"wordBanks" : {
			"SearchHugtakasafn" : { "active" : true, "order": 1 },
			"SearchIsmal" : { "active" : true, "order": 2 },
			"SearchTos" : { "active" : false, "order": 3 },
			"SearchBin" : { "active" : false, "order": 4 },
			"SearchHafro" : { "active" : false, "order": 5 },
			"SearchMalfar" : { "active" : false, "order": 6 },
			"SearchRitmalaskra" : { "active" : false, "order": 7 }			
		},
		"exact" : true
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
		if( ! oss.wordBanks) {
			oss.wordBanks = {};
		}
		$.each(ossDefaults.wordBanks, function(key, value){
			if( ! oss.wordBanks[key] ) oss.wordBanks[key] = value;
		});
		if( oss.exact === undefined ) {
			oss.exact = ossDefaults.exact;
		}
		localStorage["ordasafnasafn"] = JSON.stringify( oss );
	} else {
		oss = ossDefaults;
	}
	
	var banksInOrder = [];
	// update flip toggles
	$.each( oss.wordBanks, function(wordbank, settings){
		var $wordbankSwitch = $("select[name="+wordbank+"]");
		if( settings.active ) {
			$wordbankSwitch[0].selectedIndex = 1;
		} else {
			$wordbankSwitch[0].selectedIndex = 0;
		}
		banksInOrder.push( [wordbank, settings.order] );
	});
	// append the banks in order based on meta data
	banksInOrder.sort( function(a,b){ return a[1] - b[1]; } );
	var $bankContent = $("#oss > div[data-role=content]");
	$.each( banksInOrder, function(index, value){
		$bankContent.append( $("#"+value[0]) );
		$bankContent.append(  $("#oss .addthis_toolbox") );
	});
	
	$("#exact").attr("checked", oss.exact);

	
	function saveStateToLocalStorage() {
		if( isLocalStorage ) {
			localStorage["ordasafnasafn"] = JSON.stringify( oss );
		}
	}
	
	function searchWordbank( $wordBank ) {
		var query = $("#query").val();
		var exact = $("#exact").is(':checked');
		if( query ) {
			$wordBank.find(".results").remove();
			$wordBank.find(".searching").remove();
			var liSearching = $('<li/>', {'class': 'searching'});
			var h4 = $('<h4/>').append('<em>Leita...</em>');
			liSearching.append(h4);
			$wordBank.append( liSearching ).listview("refresh");
			
			var ordasafn = $wordBank.attr("id");
			$.ajax({
				type: 'GET',
				dataType: 'json',
				url: '/search', 
				data: { 'ordasafn' : ordasafn, 'q' : query, 'exact' : exact },
				success: function(data){
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
									//var litemParts = ['<li><a href="'+oneEntry.link+'" target="_blank">', '</a></li>'];
									var litemParts = ['<li><a href="'+oneEntry.link+'">', '</a></li>'];
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
							if( itemCount && textLegend ) h4.append( "[" + textLegend + "] " );
							h4.append( h4content.join( ', ' ) );
							var span = $('<span/>', {
								'class': 'ui-li-count',
								html: itemCount
							});
							liResults.append(h4).append(span);
							
							if( itemCount ) {
								$wordBank.find("li[class=results]").each(function(){
									if( parseInt($(this).find("span.ui-li-count").text()) < 1 ) {
										$(this).remove();
									}
								});
								
								var ul = $('<ul/>', {
									html: litems.join('')
								});
								liResults.append(ul);
	
								$wordBank.append( liResults );
							} else if( $wordBank.find("li[class=results]").size() < 1 ) {
								$wordBank.append( liResults );
							}
						});
					}
					$wordBank.listview("refresh");
				},
				error: function(jqXHR, textStatus, errorThrown) {
					$wordBank.find("h4").html('<em style="color:DarkRed;">Villa kom upp.</em>');
				}
			});			
		}
	}
	
	function updateOrderMetaData() {
		//update order metadata for localStorga
		var bankCount = 0;
		$("ul.wordbank").each(function(){
			oss.wordBanks[$(this).attr("id")].order = ++bankCount;
		});
		saveStateToLocalStorage();
	}
	
	function updateWordbankPosition( $wordBank, isOn ) {
		if( isOn ) {
			var banksToMove = [];
			$wordBank.prevAll().each(function(){
				if( $(this).find("select").val() == "off" ) {
					banksToMove.push( $(this) );
				} else {
					return false;
				}
			});
			$.each( banksToMove, function(){
				$(this).slideUp(function(){
					$(this).insertAfter( $wordBank ).slideDown(400, function(){
						updateOrderMetaData();
					});
				});
			});
		} else {
			var lastBankOn = null;
			$wordBank.nextAll().each(function(){
				if( $(this).find("select").val() == "on" ) {
					lastBankOn = $(this);
				} else {
					return false;
				}
			});
			if( lastBankOn ) {
				$wordBank.slideUp(function(){
					$(this).insertAfter( lastBankOn ).slideDown(400, function(){
						updateOrderMetaData();
					});
				});
			}
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
	
	$("#exact").change(function(event){
		if( $("#query").val() ) {
			$("#search").submit();
		}
		oss.exact = $(this).is(":checked");
		saveStateToLocalStorage();
	});
	

	var switchState = {}; // hack to handle double event firing on flip toggles, based on http://jsfiddle.net/NPC42/mTjtt/20/ <- http://stackoverflow.com/questions/6910712
	$("select[data-role=slider]").each(function(){
		var $this = $(this);
		switchState[$this.attr("id")] = $this.val();
	});
	$("#oss select").change(function(event){
		$currentSwitch = $(this);
		if( switchState[$currentSwitch.attr("id")] !== $currentSwitch.val() ) {
			$wordBank = $currentSwitch.closest("ul");
			var ordasafn = $wordBank.attr("id");
			if( $currentSwitch.val() == "on" ) {
				searchWordbank( $wordBank );
				updateWordbankPosition( $wordBank, true );
				oss.wordBanks[ordasafn].active = true;
			} else {
				$currentSwitch.closest("ul").find(".results, .searching").remove();
				updateWordbankPosition( $wordBank, false );
				oss.wordBanks[ordasafn].active = false;
			}
			saveStateToLocalStorage(); //called unnecessarily often due to asynchronisity in updateWordbankPosition() above
		}
		switchState[$currentSwitch.attr("id")] = $currentSwitch.val();
	});
	
	
	
	
	// mobile bookmark bubble init
	window.setTimeout(
		function() {
			var bubble = new google.bookmarkbubble.Bubble();

			var parameter = 'bmb=1';

			bubble.hasHashParameter = function() {
				return window.location.hash.indexOf(parameter) != -1;
			};

			bubble.setHashParameter = function() {
//				if (!this.hasHashParameter()) {
//					window.location.hash += parameter;
//				}
			};

			bubble.getViewportHeight = function() {
//				window.console.log('Example of how to override getViewportHeight.');
				return window.innerHeight;
			};

			bubble.getViewportScrollY = function() {
//				window.console.log('Example of how to override getViewportScrollY.');
				return window.pageYOffset;
			};

			bubble.registerScrollHandler = function(handler) {
//				window.console.log('Example of how to override registerScrollHandler.');
				window.addEventListener('scroll', handler, false);
			};

			bubble.deregisterScrollHandler = function(handler) {
//				window.console.log('Example of how to override deregisterScrollHandler.');
				window.removeEventListener('scroll', handler, false);
			};

			bubble.showIfAllowed();
		}, 2000);

});