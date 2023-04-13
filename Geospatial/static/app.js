console.log()


if (typeof L.canvasMarker === 'function') {
    console.log("L.canvasMarkers works");
  } else {
    console.log('L.canvasMarkers is not defined');
  }
  if (typeof noUiSlider === 'object') {
    console.log("Slider works");
  } else {
    console.log("Slider doesn't work");
  }
  


document.getElementById("ClearPoints").addEventListener("click", ClearPoints);
document.getElementById("PlotRelevantPoints").addEventListener("click", PlotRelPoints);
document.getElementById("PlotDistricts").addEventListener("click", PlotDisticts);
document.getElementById("PlotZIPCODE").addEventListener("click", PlotZipCodes);
document.getElementById("PlotBars").addEventListener("click", PlotBars);
document.getElementById('SelectByDistrictButton').addEventListener('click', SelectByButtonClicked);
document.getElementById('SelectByZipCodeButton').addEventListener('click', SelectByButtonClicked);

document.getElementById("Monday").addEventListener("click", toggleButton);
document.getElementById("Tuesday").addEventListener("click", toggleButton);
document.getElementById("Wednesday").addEventListener("click", toggleButton);
document.getElementById("Thursday").addEventListener("click", toggleButton);
document.getElementById("Friday").addEventListener("click", toggleButton);
document.getElementById("Saturday").addEventListener("click", toggleButton);


function toggleButton(event) { // Function to toggle "pressed" on buttons when pressed
  event.target.classList.toggle("pressed");
}


var TODslider = document.getElementById('TimeOfDaySlider');
noUiSlider.create(TODslider, {
start: [0, 100], // Initial values of the handles
connect: true, // Connect the handles with a colored bar
range: {
    'min': 0,
    'max': 100
}
});

TODslider.noUiSlider.on('update', function(values) {
var min = values[0];
var max = values[1];
console.log('Selected min value: ' + min);
console.log('Selected max value: ' + max);});

var checkboxes = document.getElementsByClassName('FilterCheck');

// Function to handle button click
function SelectByButtonClicked(event) {
  const clickedButton = event.target;
  // Remove 'active' class from all buttons
  const buttons = document.getElementsByClassName('SelectButtons');
  for (let i = 0; i < buttons.length; i++) {
    buttons[i].classList.remove('active');
  }
  // Add 'active' class to clicked button
  clickedButton.classList.add('active');
}

var ShotSpotterFilterApply = false;
document.getElementById("ShotSpotterFilterCheck").addEventListener("change", //ShotSpotter Only Filter
function(){
    if(this.checked){
        ShotSpotterFilterApply = true;
        document.getElementById("PatrolFilterCheck").checked = false;
        PatrolFilterApply = false;
        ApplyFilters();
    } else{
        ShotSpotterFilterApply = false;
        ApplyFilters();
    }
});

var PatrolFilterApply = false;
document.getElementById("PatrolFilterCheck").addEventListener("change", //Patrol Only Filter
function(){
    if(this.checked){
        PatrolFilterApply = true;
        document.getElementById("ShotSpotterFilterCheck").checked = false;
        ShotSpotterFilterApply = false;
        ApplyFilters();
    } else{
        PatrolFilterApply = false;
        ApplyFilters();
    }
});

var PDColorApply = false;
document.getElementById("ColorCheckPD").addEventListener("change", function() { // Update ID to match the HTML
    if (this.checked) {
        PDColorApply = true;
        document.getElementById("ColorCheckCallDensity").checked = false; // Update ID to match the HTML
        CallDensityColorApply = false;
    } else {
        PDColorApply = false;
    }
});

var CallDensityColorApply = true;
document.getElementById("ColorCheckCallDensity").addEventListener("change", function() { // Update ID to match the HTML
    if (this.checked) {
        CallDensityColorApply = true;
        document.getElementById("ColorCheckPD").checked = false; // Update ID to match the HTML
        PDColorApply = false;
    } else {
        CallDensityColorApply = false;
    }
});


var map = L.map('map', {preferCanvas: true}).setView([43.0389, -87.9065], 10);  

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
}).addTo(map);

var DisplayedRecords = L.layerGroup().addTo(map);
var filteredData = [];

let CallDensityScaling = 0;

function UpdateConstants(){
    return fetch('/data') // fetch data from Flask and return the promise
    .then(response => response.json()) // parse response as JSON
    .then(data => {
        const CallDensityColumn = data.map(record =>  parseFloat(record[12]));
        CallDensityScaling = 1/ Math.max(...CallDensityColumn);
        console.log(`The Call Density Scaling is: ${CallDensityScaling}`);
    })
    .catch(error => console.error(error)); // handle errors
}

//Initialize
ApplyFilters();
document.getElementById('ColorCheckCallDensity').checked = true; // Update ID to match the HTML
PlotRelPoints();



function ClearPoints() {
    DisplayedRecords.clearLayers();
}

function Filters(record) {
//TODO Maybe precompute some of these filters
    if(ShotSpotterFilterApply == true){
        return record[8] == "SHOTSPOTTER";
    }
    if(PatrolFilterApply == true){
        const PatrolList = ["BUSINESS CHECK", "PATROL","PARK AND WALK","TAVERN CHECK","SCHL MONITORING"];
        return PatrolList.includes(record[8]);
    }
    return true;
}

function ApplyFilters(){
    fetch('/data')
    .then(response => response.json())
    .then(data => {
        window.filteredData = data.filter(item => {
        return Filters(item)
    });
    });
}

function ColorFunction(record,CDS){
    if(PDColorApply == true){
        switch (record[7]) {
            case '1':
            return  'orange';
            case '2':
            return 'green';
            case '3':
            return 'blue';
            case '4':
            return 'purple';
            case '5':
            return 'blue';
            case '6':
            return 'red';
            case '7':
            return 'yellow';
            default:
            return 'white';
        }
    }else if(CallDensityColorApply == true){
        const ColorScale = chroma.scale(['yellow', 'navy']).mode('lch');
        return ColorScale(record[12] * CDS);
    } else {
        return 'blue'
    }
}

var SelectedMarker = null;
function MakerClicked(e) {
    console.log(e.latlng);
    console.log(e.target.LocationData);
    var location = e.target.LocationData

    if(SelectedMarker !== null){
        SelectedMarker.setStyle({
            fillOpacity: .2
        });
    }
    SelectedMarker = e.target
    SelectedMarker.setStyle({
        fillOpacity: .7,
      });
    SelectedMarker.bringToBack();

    var SelectedCallPrintout = document.getElementById("SelectedCallPrintout");
    SelectedCallPrintout.style.whiteSpace = 'pre-wrap';
    var ID = [];
    var NATUREOFCALL = [];
    var TIME = [];
    window.filteredData.forEach(row => {
        if(row[1] == location){
            ID.push(row[0]);
            NATUREOFCALL.push(row[8])
            TIME.push((new Date(Date.parse(row[6]))).getHours())
        }
    })

    //SELECTED BARGRAPH
    var NATUREOFCALLCounts = {};
    NATUREOFCALL.forEach(function(NOC) {
        if (NOC in NATUREOFCALLCounts) {
            NATUREOFCALLCounts[NOC]++;
        } else {
            NATUREOFCALLCounts[NOC] = 1;
        }
    });
    SelectedCallPrintout.innerHTML = (
    "IDs: "+ ID.join(' ')
    );
    var Trace = {
        x:  Array.from(new Set(NATUREOFCALL)),
        y: Object.values(NATUREOFCALLCounts),
        type: 'bar',
        orientation: 'v'
      };
      var Data = [Trace];
      var Layout = {
        title: 'Bargraph at Selection',
        margin:{t: 30},
        xaxis: {title: 'Nature of Call'},
        yaxis: {title: 'Count'}
      };
      Plotly.newPlot('SelectedCallsPlot', Data, Layout,{displayModeBar: false});
    
    //SELECTED TIME HIST

    var TickVals = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5]; 
    var TickText = ['12:00 am', '1:00 am', '2:00 am', '3:00 am', '4:00 am', '5:00 am', '6:00 am', '7:00 am', '8:00 am', '9:00 am', '10:00 am', '11:00 am', '12:00 pm', '1:00 pm', '2:00 pm', '3:00 pm', '4:00 pm', '5:00 pm', '6:00 pm', '7:00 pm', '8:00 pm', '9:00 pm', '10:00 pm', '11:00 pm'];
    var TraceTime = {
        x:  TIME,
        autobinx: false,
        type: 'histogram',
        orientation: 'v',
        xbins: { 
            end: 24,
            size: 1, 
            start: 0
        },
        hovertemplate: "%{y} Records<extra></extra>"
    };
    var DataTime = [TraceTime];
    var LayoutTime = {
        title: {text: 'Time of Call', font: {size: 15}},
        margin:{t: 30},
        bargap: 0.05,
        xaxis: {
            title: 'Time',
            margin:{t: 20},
            range: [0, 24],
            dtick: 1,
            tickmode: 'array',
            tickvals: TickVals,
            ticktext: TickText,
            tickangle: 90
        },
        hovermode: 'closest',
        yaxis: {title: '',
        nticks: 2},
        height: 150
    };
    Plotly.newPlot('SelectedCallsTimeHist', DataTime, LayoutTime,{displayModeBar: false});
      
}


function PlotRelPoints() {
    DisplayedRecords.clearLayers();
    var PlottedLocations = {};
    UpdateConstants().then(() => {
        console.log(`Call Density Scaling: ${CallDensityScaling}`);
        const policeStationsList = ['6929 W SILVER SPRING DR,MKE', '749 W STATE ST,MKE', '4715 W VLIET ST,MKE', '6929 W SILVER SPRING DR,MKE','3626 W FOND DU LAC AV,MKE', '2333 N 49TH ST,MKE','2920 N VEL R PHILLIPS AV,MKE','245 W LINCOLN AV,MKE','3006 S 27TH ST,MKE'];
        //TODO replace this next chunk with just plotting admin locations directly regardless of whether they are in data? or make small check
        //TODO FLIP admin and normal locations so can see admin over points
        window.filteredData.forEach(row => {
        if (policeStationsList.includes(row[1])) {
            const location = row[1];
            if (!PlottedLocations[location]) {
                PlottedLocations[location] = true;
                const policeStations = L.canvasMarker(L.latLng(row[2], row[3]),
                { img: {
                    url: '/static/star-filled.png',
                    size: [20, 20],     //image size ( default [40, 40] )
                    //rotate: 10,         //image base rotate ( default 0 )
                    //offset: { x: 0, y: 0 }, //image offset ( default { x: 0, y: 0 } )
                },}).addTo(DisplayedRecords);
                policeStations.bindPopup(row[1]);
            }
        }
        });
        const locationCounts = {};
        window.filteredData.filter(row => !policeStationsList.includes(row[1])).forEach(row => {
            const location = row[1];
            locationCounts[location] = (locationCounts[location] || 0) + 1;
        });
        window.filteredData.filter(row => !policeStationsList.includes(row[1])).forEach(row => {
            const location = row[1];
            if (!PlottedLocations[location]) {
                PlottedLocations[location] = true;
                const radius = 10 + (locationCounts[location]**.5) * 10;
                const markerCOS = L.circle([row[2], row[3]],
                    {   stroke: true,
                        opacity	: .6,
                        weight: 2,
                        color: chroma(ColorFunction(row,CallDensityScaling)).darken().hex(),
                        fillOpacity	: .2,
                        fillColor: ColorFunction(row,CallDensityScaling)
                    }).setRadius(radius).addTo(DisplayedRecords).on('click', MakerClicked);
                markerCOS.LocationData = location;
                markerCOS.bindPopup(row[1]);
            }
        });
    });
}

function PlotDisticts() {
    fetch('/geojson')
        .then(response =>response.json())
        .then(geojson => {
            L.geoJSON(geojson, {
                style: {
                    color: 'Black',
                    fillColor: 'grey',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: .05,
                },
                onEachFeature: function (feature, layer) {
                    //console.log(feature.properties.POLICE)
                    layer.bindPopup('District: ' + feature.properties.POLICE);
                }}).addTo(DisplayedRecords);
        })
}

function PlotZipCodes() {
    fetch('/geojsonZIPCODES')
        .then(response =>response.json())
        .then(geojson => {
            L.geoJSON(geojson, {
                style: {
                    color: 'Black',
                    fillColor: 'grey',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: .05,
                },
                onEachFeature: function (feature, layer) {
                    //console.log(feature.properties.POLICE)
                    layer.bindPopup('District: ' + feature.properties.ZCTA5CE10);
                }}).addTo(DisplayedRecords);
        })
}


function PlotBars() {
    fetch('/bars')
        .then(response =>response.json())
        .then(geojson => {
            L.geoJSON(geojson, {
                    pointToLayer: function (feature, latlng) {
                        return L.canvasMarker(L.latLng(latlng), { img: {
                            url: '/static/baricon.png',
                            size: [10, 10],
                        }})
                    },
                onEachFeature: function (feature, layer) {
                    layer.bindPopup('Bar: ' + feature.properties.name);
                }}).addTo(DisplayedRecords);
        })
        .catch(error => {
            console.log(error); // log any errors
        });
}


// function onMapClick(e) {
//     popup
//         .setLatLng(e.latlng)
//         .setContent(`You clicked the map at ${e.latlng.toString()}`)
//         .openOn(map);
// }

// map.on('click', onMapClick);



