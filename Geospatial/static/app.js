console.log()
// import { canvasMarker } from 'leaflet-canvas-markers';

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


var map = L.map('map', {preferCanvas: true}).setView([43.0389, -87.9065], 10);  

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
}).addTo(map);

var DisplayedRecords = L.layerGroup().addTo(map);

//L.canvasMarkerLayer({}).addTo(DisplayedRecords);

function ClearPoints() {
    DisplayedRecords.clearLayers();
}

fetch('/data')
    .then(response => response.json())
    .then(data => {
        data.forEach(row => {
            let marker = L.marker([row[2], row[3]]).addTo(DisplayedRecords);
            marker.bindPopup(row[1]);
        });
    });


function PlotPoints() {
    var locationCounts = {};
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            data.forEach(row => {
                var location = row[1];
                locationCounts[location] = (locationCounts[location] || 0) + 1;
                var radius = locationCounts[location] / 4 * 10;
                var markerCOS = L.circle([row[2], row[3]]).setRadius(radius).addTo(DisplayedRecords);
                markerCOS.bindPopup(row[1]);
            });
        });
}

function PlotRelPoints() {
    const policeStationsList = ['6929 W SILVER SPRING DR,MKE', '749 W STATE ST,MKE', '4715 W VLIET ST,MKE', '6929 W SILVER SPRING DR,MKE','3626 W FOND DU LAC AV,MKE', '2333 N 49TH ST,MKE','2920 N VEL R PHILLIPS AV,MKE','245 W LINCOLN AV,MKE','3006 S 27TH ST,MKE'];
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            data.forEach(row => {
                if (policeStationsList.includes(row[1])) {
                    const policeStations = L.canvasMarker(L.latLng(row[2], row[3]),
                    { img: {
                        url: '/Geospatial/static/star-filled.png',
                        size: [20, 20],     //image size ( default [40, 40] )
                        //rotate: 10,         //image base rotate ( default 0 )
                        //offset: { x: 0, y: 0 }, //image offset ( default { x: 0, y: 0 } )
                    },}).addTo(DisplayedRecords);
                    policeStations.bindPopup(row[1]);
                }
            });
            const locationCounts = {};
            data.filter(row => !policeStationsList.includes(row[1])).forEach(row => {
                const location = row[1];
                locationCounts[location] = (locationCounts[location] || 0) + 1;
            });
            data.filter(row => !policeStationsList.includes(row[1])).forEach(row => {
                const location = row[1];
                const radius = 10 + locationCounts[location] / 2 * 10;
                const markerCOS = L.circle([row[2], row[3]]).setRadius(radius).addTo(DisplayedRecords);
                markerCOS.bindPopup(row[1]);
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
                            url: '/Geospatial/static/baricon.png',
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



