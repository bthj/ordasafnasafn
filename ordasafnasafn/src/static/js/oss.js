
$(document).bind("mobileinit", function(){
	$.mobile.page.prototype.options.addBackBtn = true;
	$.mobile.page.prototype.options.backBtnText = "Til baka";
	
	$.mobile.allowCrossDomainPages = true;
});



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
	
	var ossNameIdMap = {
			"SearchHugtakasafn" : 1, 
			"SearchIsmal" : 2,
			"SearchTos" : 3, 
			"SearchBin" : 4, 
			"SearchHafro" : 5, 
			"SearchMalfar" : 6, 
			"SearchRitmalaskra" : 7 
	};
	
	var defaultLocale = "en";
	
	
	if( typeof(PhoneGap) == 'undefined' ) {
		var hostUrl = location.protocol + "//" + location.host + location.pathname;
		var localePathPrefix = "/static/lang";
	} else {
		var hostUrl = "http://oss.nemur.net/";
		var localePathPrefix = "lang";
		
		$("a[rel*=external]").live('click', function(event){	
			navigator.app.loadUrl($(this).attr('href'), {openexternal:true});
			return false;
		});
		
		$("div#oss").live('pageshow', function(event,ui){
			// let's open a dialog with data charges alert if not opened before
			if( isLocalStorage && ! localStorage["ossIsChargeInfoDisplayed"] ) {
				$.mobile.changePage( "#charges", { transition: "pop", role: "dialog", reverse: false }  );
				localStorage["ossIsChargeInfoDisplayed"] = true;
			}		
		});
	}
	

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
	
	
	
	var bankIdsFromQuery = getQueryString()["b"];
	if( bankIdsFromQuery ) {
		// we are setting active banks via query parameter, let those override
		var bankIds = bankIdsFromQuery.split("|");

		var order = 0;
		$.each( oss.wordBanks, function(wordbank, settings){
			oss.wordBanks[wordbank].active = false;
			$.each( bankIds, function( index, oneId ){
				if( oneId == ossNameIdMap[wordbank] ) {
					oss.wordBanks[wordbank].active = true;
					oss.wordBanks[wordbank].order = ++order;
				}
			});			
		});
		$.each( oss.wordBanks, function(wordbank, settings){
			if( false == settings.active ) {
				oss.wordBanks[wordbank].order = ++order;
			}
		});
		
		var exactFromQuery = getQueryString()["e"];
		if( exactFromQuery == 't' ) {
			oss.exact = true;
		} else {
			oss.exact = false;
		}
		
		saveStateToLocalStorage();
	}
	
	
	
	var localeFromQuery = getQueryString()["locale"];
	if( localeFromQuery ) {
		saveLocale( localeFromQuery )
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
	});
	
	$("#exact").attr("checked", oss.exact);

	
	
	function saveLocale( locale ) {
		oss.locale = locale;
		saveStateToLocalStorage();
	}
	function applyLocale( locale ) {
		var opts = { language: locale, pathPrefix: localePathPrefix };
		$("[rel*=localize]").localize("oss", opts);
		
		
		$('input:radio[name=interface-language]').filter('[value='+locale+']').attr('checked', true);
		
		$.mobile.page.prototype.options.backBtnText = $.localize.data.oss['Back'];
	}
	
	
	function getActiveBankIds() {
		var activeIds = [];
		$.each( oss.wordBanks, function(wordbank, settings){
			if( oss.wordBanks[wordbank].active ) {
				activeIds.push( ossNameIdMap[wordbank] );	
			}
		});
		return activeIds;
	}
	
	
	function updateSearchLink( query ) {
		if( query ) {
			// var searchUrl = location.protocol + "//" + location.host + location.pathname
			var searchUrl = hostUrl
				+ "?q=" + query + "&b=" + getActiveBankIds().join("|")
				+ "&e=" + (oss.exact ? "t" : "f");
			$( "#searchlink" ).attr( "href", searchUrl );
			$( "#searchlink" ).show();			
		}
	}

	
	function getQueryString() {  // snatched from http://stackoverflow.com/questions/647259/javascript-query-string/647272#647272
		var result = {}, queryString = location.search.substring(1),
			re = /([^&=]+)=([^&]*)/g, m;

		while (m = re.exec(queryString)) {
			result[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
		}
		return result;
	}
	
	function saveStateToLocalStorage() {
		if( isLocalStorage ) {
			localStorage["ordasafnasafn"] = JSON.stringify( oss );
		}
	}
	
	
	function searchWordbank( $wordBank ) {
		var query = $("#query").val();
		var exact = $("#exact").is(':checked');
		if( query ) {
			$wordBank.find(".results").each(function(){
				var nestedListLink = $(this).find("a:first");
				$(this).remove();
				// hack to remove divs for nested lists from previous results - should be removed by the JQM framework?
				var dataUrl = nestedListLink.attr("href").substring(1);
				$("div[data-role=page]").each(function(){
					if( $(this).attr("data-url") == dataUrl ) {
						$(this).remove();
					}
				});
			});
//			$wordBank.find(".results").remove();			
			$wordBank.find(".searching").remove();
			
			var liSearching = $('<li/>', {'class': 'searching'});
			var h4 = $('<h4/>').append('<em>'+$.localize.data.oss['Searching']+'...</em>');
			liSearching.append(h4);
			$wordBank.append( liSearching ).listview("refresh");
			
			var ordasafn = $wordBank.attr("id");
			$.ajax({
				type: 'GET',
				dataType: 'json',
				url: hostUrl + 'search', 
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
									var litemParts = ['<li><a href="'+oneEntry.link+'" target="_blank" rel="external">', '</a></li>'];
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
		
		updateSearchLink( query );
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
	
	function searchWordbanks() {
		$("ul.wordbank").each(function(){
			var $wordBank = $(this);
			var isActive = $wordBank.find("select").val() == "on";
			if( isActive ) searchWordbank( $wordBank );
		});		
	}
	
	$("#search").submit(function(event){
		searchWordbanks();
		
		return false;
	});
	
	$("#exact").change(function(event){
		oss.exact = $(this).is(":checked");
		if( $("#query").val() ) {
			$("#search").submit();
		}
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
				updateWordbankPosition( $wordBank, true );
				oss.wordBanks[ordasafn].active = true;
				searchWordbank( $wordBank );
			} else {
				$currentSwitch.closest("ul").find(".results, .searching").remove();
				updateWordbankPosition( $wordBank, false );
				oss.wordBanks[ordasafn].active = false;
				updateSearchLink( $("#query").val() );
			}
			saveStateToLocalStorage(); //called unnecessarily often due to asynchronisity in updateWordbankPosition() above
		}
		switchState[$currentSwitch.attr("id")] = $currentSwitch.val();
	});
	
	
	
	$("input[name=interface-language]").change(function(event){
		
		saveLocale( $(this).val() );
		
		window.location.href = window.location.pathname;
	});

	

	$( '#oss' ).bind( 'pagebeforecreate',function(event){
		if( ! oss.locale ) {
			saveLocale( defaultLocale );
		}
		applyLocale( oss.locale );
		$("#search-btn").attr( 'value', $.localize.data.oss['Search'] );
	});	
	
	
	
	//TODO: look at:  http://jquerymobile.com/test/docs/pages/page-dynamic.html
	// let's make sure the page is initialized... 
	$("#oss").page();
	$("#searchlink").hide();
	
	// ...before we call methods to refresh it's widgets:
	var query = getQueryString()["q"];
	if( query ) {
		$("#query").val( query );
		searchWordbanks();
	}
	
	
	
	if( typeof(PhoneGap) == 'undefined' ) {
		// mobile bookmark bubble init
		window.setTimeout(
			function() {
				var bubble = new google.bookmarkbubble.Bubble();

				var parameter = 'bmb=1';

				bubble.hasHashParameter = function() {
					return window.location.hash.indexOf(parameter) != -1;
				};

				bubble.setHashParameter = function() {
//					if (!this.hasHashParameter()) {
//						window.location.hash += parameter;
//					}
				};

				bubble.getViewportHeight = function() {
//					window.console.log('Example of how to override getViewportHeight.');
					return window.innerHeight;
				};

				bubble.getViewportScrollY = function() {
//					window.console.log('Example of how to override getViewportScrollY.');
					return window.pageYOffset;
				};

				bubble.registerScrollHandler = function(handler) {
//					window.console.log('Example of how to override registerScrollHandler.');
					window.addEventListener('scroll', handler, false);
				};

				bubble.deregisterScrollHandler = function(handler) {
//					window.console.log('Example of how to override deregisterScrollHandler.');
					window.removeEventListener('scroll', handler, false);
				};

				bubble.showIfAllowed();
			}, 2000);		
	}


});
