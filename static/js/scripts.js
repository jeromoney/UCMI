/**
 * scripts.js
 *
 * Computer Science 50
 * Final Project
 *
 * Global JavaScript.
 */
// Globals
var map;
var viewMarkers = [];
var viewNum = -1;
// Set your custom overlay object's prototype to a new instance of google.maps.OverlayView(). In effect, this will subclass the overlay class.
var overlay;
radarOverlay.prototype = new google.maps.OverlayView();

// initialize checkbox
$("[name='editCheckbox']").bootstrapSwitch();
$("[name='showView']").bootstrapSwitch();

$('input[name="showView"]').on('switchChange.bootstrapSwitch', function(event, state) {
  showView();
});


$(document).ready(function(){
    $('#altFilter').click(function() {
        altitudeFilter();
    })
});

$(document).ready(function(){
    $('#altRefresh').click(function() {
        altitudeRefresh();
    })
});

$(document).ready(function(){
    $('#showView').click(function() {
        showView();
    })
});

function initialize() {
   initMap();
   initAutoComplete();
}


function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
            center: {lat: 38.532138, lng: -105.992014},
            zoom: 13,
            mapTypeId: 'roadmap'
        });
        
}

// This example adds a search box to a map, using the Google Place Autocomplete
      // feature. People can enter geographical searches. The search box will return a
      // pick list containing a mix of places and predicted search terms.

      // This example requires the Places library. Include the libraries=places
      // parameter when you first load the API. For example:
      // <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places"> 
function initAutoComplete() {

        

        // Create the search box and link it to the UI element.
        var input = document.getElementById('pac-input');
        var searchBox = new google.maps.places.SearchBox(input);
        map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);

        // Bias the SearchBox results towards current map's viewport.
        map.addListener('bounds_changed', function() {
          searchBox.setBounds(map.getBounds());
        });

        var markers = [];
        // Listen for the event fired when the user selects a prediction and retrieve
        // more details for that place.
        searchBox.addListener('places_changed', function() {
          var places = searchBox.getPlaces();

          if (places.length == 0) {
            return;
          }

          // Clear out the old markers.
          markers.forEach(function(marker) {
            marker.setMap(null);
          });
          markers = [];

          // For each place, get the icon, name and location.
          var bounds = new google.maps.LatLngBounds();
          places.forEach(function(place) {
            if (!place.geometry) {
              console.log("Returned place contains no geometry");
              return;
            }
            var icon = {
              url: place.icon,
              size: new google.maps.Size(71, 71),
              origin: new google.maps.Point(0, 0),
              anchor: new google.maps.Point(17, 34),
              scaledSize: new google.maps.Size(25, 25)
            };

            // Create a marker for each place.
            markers.push(new google.maps.Marker({
              map: map,
              icon: icon,
              title: place.name,
              position: place.geometry.location
            }));

            if (place.geometry.viewport) {
              // Only geocodes have viewport.
              bounds.union(place.geometry.viewport);
            } else {
              bounds.extend(place.geometry.location);
            }
          });
          map.fitBounds(bounds);
        });
        
        // Listen for map clicks
        map.addListener('click', function(event) {
            var editState = $('input[name="editCheckbox"]').bootstrapSwitch('state');
            
            // If edit button is checked
            if ($('input[name="editCheckbox"]').bootstrapSwitch('state')){
                returnLocation(event);
            };
            
            });
            

}
        

       
 
      
// When user clicks on map, marker is created and then triggers viewshed calculation
function returnLocation(event) {
    var dateStamp = Date.now();
    var latLng = event.latLng;
    var marker = new google.maps.Marker({
        position: latLng,
        map: map,
    });
    viewMarkers.push(marker)
    viewNum ++;
    var altitude = getAltitude();
    var greaterthan = $("#altFilter").val();
    var parameters = {
        dateStamp: dateStamp,
        lat: latLng.lat(),
        lng: latLng.lng(),
        size: viewMarkers.length,
        viewNum: viewNum,
        altitude : altitude,
        greaterthan : greaterthan
    };
    
    var callback = function (){
       checkFlag(dateStamp );
        };
    
    // Sends lat lon to python script
    $.ajax({
        url: "python",
        method: "POST",
        data: parameters,
        }).done( callback());
};

// Queries server every second to see if GIS processing is done
function checkFlag(dateStamp) {
        if(isTaskDone(dateStamp) == false) {
            showProgressBar(true);
            window.setTimeout(checkFlag, 1000 ,  dateStamp); /* this checks the flag every 1000 milliseconds*/
        } else {
            showProgressBar(false);
            showImage();
    }
}

// Shows and hides progress bar
function showProgressBar(show) {
       if (show){
           // show progress bar
            $("#progress").removeClass('hidden');
       }
       else {
           // hide progress bar
           $("#progress").addClass('hidden');
       };
}

// Toggles viewshed on/off
function showView(){
    // if state is false. show view
    var state = $('input[name="showView"]').bootstrapSwitch('state');
    if (typeof overlay != 'undefined'){
        if (state){
            // hide view
            overlay.hide();
            }
        else{
            // hide view
            overlay.show();
        }
    }
}


// Returns true if task is finished
function isTaskDone(dateStampCheck){
    var data = $.ajax({
        url: 'isTaskDone/' + dateStampCheck,
        async: false,
        dataType: 'json'}).responseJSON;
        return data['done'];
}


// Create a constructor for your custom overlay, and set any initialization parameters.
/** @constructor */
function radarOverlay(bounds, image, map) {

    // Initialize all properties.
    this.bounds_ = bounds;
    this.image_ = image;
    this.map_ = map;
    
    // Define a property to hold the image's div. We'll
    // actually create this div upon receipt of the onAdd()
    // method so we'll leave it null for now.
    this.div_ = null;
    
    // Explicitly call setMap on this overlay.
    this.setMap(map);
}


function showImage(){
    var srcImage = '../viewsheds/commonviewshed' + viewNum + '.png' + "?lastmod=" + Date.now();
    if (typeof overlay != 'undefined'){
        overlay.refreshImage(srcImage);
    }
    else{
        // The custom radarOverlay object contains the radar image,
        // the bounds of the image, and a reference to the map.
        // Get the bounds from JSON file
        var data = $.ajax({
            url: '../viewsheds/commonviewshed' + viewNum + '.json' + "?lastmod=" + Date.now(),
            async: false,
            dataType: 'json'}).responseJSON;


        east = parseFloat(data['east']);
        west = parseFloat(data['west']);
        south = parseFloat(data['south']);
        north = parseFloat(data['north']);

        var bounds = new google.maps.LatLngBounds( {lat: south, lng: west} , 
           {lat: north, lng: east}
        );


            radarOverlay.prototype = new google.maps.OverlayView();
            overlay = new radarOverlay(bounds, srcImage, map); 
    };


    
    // Implement an onAdd() method within your prototype, and attach the overlay to the map. OverlayView.onAdd() will be called when the map is ready for the overlay to be attached.
    
    /**
    * onAdd is called when the map's panes are ready and the overlay has been
    * added to the map.
    */
    radarOverlay.prototype.onAdd = function() {
    
        var div = document.createElement('div');
        div.style.borderStyle = 'none';
        div.style.borderWidth = '0px';
        div.style.position = 'absolute';
        
        // Create the img element and attach it to the div.
        var img = document.createElement('img');
        img.src = this.image_;
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.position = 'absolute';
        div.appendChild(img);
        
        this.div_ = div;
        
        // Add the element to the "overlayLayer" pane.
        var panes = this.getPanes();
        panes.overlayLayer.appendChild(div);
    };
    
    
    // Implement a draw() method within your prototype, and handle the visual display of your object. OverlayView.draw() will be called when the object is first displayed.
    radarOverlay.prototype.draw = function() {
        
        // We use the south-west and north-east
        // coordinates of the overlay to peg it to the correct position and size.
        // To do this, we need to retrieve the projection from the overlay.
        var overlayProjection = this.getProjection();
        
        // Retrieve the south-west and north-east coordinates of this overlay
        // in LatLngs and convert them to pixel coordinates.
        // We'll use these coordinates to resize the div.
        var sw = overlayProjection.fromLatLngToDivPixel(this.bounds_.getSouthWest());
        var ne = overlayProjection.fromLatLngToDivPixel(this.bounds_.getNorthEast());
        
        // Resize the image's div to fit the indicated dimensions.
        var div = this.div_;
        div.style.left = sw.x + 'px';
        div.style.top = ne.y + 'px';
        div.style.width = (ne.x - sw.x) + 'px';
        div.style.height = (sw.y - ne.y) + 'px';
    };        

      // Set the visibility to 'hidden' or 'visible'.
      radarOverlay.prototype.hide = function() {
        if (this.div_) {
          // The visibility property must be a string enclosed in quotes.
          this.div_.style.visibility = 'hidden';
        }
      };

      radarOverlay.prototype.show = function() {
        if (this.div_) {
          this.div_.style.visibility = 'visible';
        }
      };

    // The onRemove() method will be called automatically from the API if
    // we ever set the overlay's map property to 'null'.
    radarOverlay.prototype.onRemove = function() {
      this.div_.parentNode.removeChild(this.div_);
      this.div_ = null;
    };
    
    
    radarOverlay.prototype.refreshImage = function(imageSRC){
    // adding last mode to prevent browser caching
    this.image_ = imageSRC;
    this.setMap(null);
    this.setMap(this.map_);

    }
}



function altitudeFilter(){
    if ($("#altFilter").text() == '<'){
        $("#altFilter").text('>');
        $("#altFilter").val('greaterthan');
    }
    else{
        $("#altFilter").text('<');
        $("#altFilter").val('lessthan');
    }
};


// Need to add form verification

function altitudeRefresh(){
    viewNum ++;
    var greaterthan = $("#altFilter").val();
    var altitude = getAltitude();
    dateStamp = Date.now();
    var callback = function (){
        checkFlag(dateStamp );
        };
    var parameters = {
        dateStamp : dateStamp,
        altitude: altitude,
        greaterthan: greaterthan,
        viewNum: viewNum
    };
    $.ajax({
        url: "elevationfilter",
        method: "POST",
        data: parameters,
        }).done(callback);
}


function getAltitude(){
    var altitude = $("#altitude").val();
    if (altitude == ""){
        altitude = "0";
    }
    // User entered a non-number   
    if (isNaN(altitude)){
        var altFilter = $("#altFilter").val();
        if (altFilter == 'greaterthan'){
            altitude = "0";
        }
        else {
            altitude = "30000";
        };
        // Change color to red to indicate error
        $("#altitude").addClass('alert alert-danger');
    }
    else {
        // all is good so remove alert class
        $("#altitude").removeClass('alert alert-danger');
    }
    
    // conver feet to meters
    return altitude * 0.3048;
}



initialize();
