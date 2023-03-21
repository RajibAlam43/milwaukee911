console.log()


if (typeof L.canvasMarker === 'function') {
    console.log("L.canvasMarkers works");
  } else {
    console.log('L.canvasMarkers is not defined');
  }


document.getElementById("ClearPoints").addEventListener("click", ClearPoints);
document.getElementById("PlotPoints").addEventListener("click", PlotPoints);
document.getElementById("PlotRelevantPoints").addEventListener("click", PlotRelPoints);
document.getElementById("PlotDistricts").addEventListener("click", PlotDisticts);
document.getElementById("PlotBars").addEventListener("click", PlotBars);

var ShotSpotterFilterApply = false;
document.getElementById("ShotSpotterFilterCheck").addEventListener("change", //ShotSpotter Only Filter
function(){
    if(this.checked){
        ShotSpotterFilterApply = true;
        ApplyFilters();
    } else{
        ShotSpotterFilterApply = false;
        ApplyFilters();
    }
});

var PDColorApply = false;
document.getElementById("PDColorCheck").addEventListener("change", //Toggle Coloring Markers by Police District
function(){
    if(this.checked){
        PDColorApply = true;
        document.getElementById("CallDensityColorCheck").checked = false;
        CallDensityColorApply = false;
    } else{
        PDColorApply = false;
    }
});

var CallDensityColorApply = false;
document.getElementById("CallDensityColorCheck").addEventListener("change", //Toggle Coloring Markers by Call Density
function(){
    if(this.checked){
        CallDensityColorApply = true;
        document.getElementById("PDColorCheck").checked = false;
        PDColorApply = false;
    } else{
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
        const CallDensityColumn = data.map(record =>  parseFloat(record[6]));
        CallDensityScaling = 1/ Math.max(...CallDensityColumn);
        console.log(`The Call Density Scaling is: ${CallDensityScaling}`);
    })
    .catch(error => console.error(error)); // handle errors
}

ApplyFilters();



function ClearPoints() {
    DisplayedRecords.clearLayers();
}

function Filters(record) {
//TODO Maybe precompute some of these filters
    if(ShotSpotterFilterApply == true){
        return record[5] == "SHOTSPOTTER";
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
        switch (record[4]) {
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
        return ColorScale(record[6] * CDS);
    } else {
        return 'blue'
    }
}


function PlotPoints() {
    var locationCounts = {};
    var PlottedLocations = {};
    UpdateConstants().then(() => {
        console.log(`Call Density Scaling: ${CallDensityScaling}`);
    window.filteredData.forEach(row => {
        var location = row[1];
        locationCounts[location] = (locationCounts[location] || 0) + 1;
    });
    window.filteredData.forEach(row => {
        var location = row[1];
        if (!PlottedLocations[location]) {
            PlottedLocations[location] = true;
            var radius = locationCounts[location] / 4 * 10;
            var markerCOS = L.circle([row[2], row[3]],
                {   stroke: true,
                    opacity	: .6,
                    color: chroma(ColorFunction(row,CallDensityScaling)).darken().hex(),
                    fillOpacity	: .2,
                    fillColor: ColorFunction(row,CallDensityScaling)
                }).setRadius(radius).addTo(DisplayedRecords);
            markerCOS.bindPopup(row[1]);
        }
    });
});    
}

function PlotRelPoints() {
    var PlottedLocations = {};
    UpdateConstants().then(() => {
        console.log(`Call Density Scaling: ${CallDensityScaling}`);
        const policeStationsList = ['6929 W SILVER SPRING DR,MKE', '749 W STATE ST,MKE', '4715 W VLIET ST,MKE', '6929 W SILVER SPRING DR,MKE','3626 W FOND DU LAC AV,MKE', '2333 N 49TH ST,MKE','2920 N VEL R PHILLIPS AV,MKE','245 W LINCOLN AV,MKE','3006 S 27TH ST,MKE'];
        //TODO replace this next chunk with just plotting admin locations directly regardless of whether they are in data? or make small check
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
                    }).setRadius(radius).addTo(DisplayedRecords);
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



