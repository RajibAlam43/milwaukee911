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



document.getElementById("PlotRelevantPoints").addEventListener("click", PlotRelPoints);
document.getElementById("PlotBars").addEventListener("click", PlotBars);

document.getElementById("Monday").addEventListener("click", toggleButton);
document.getElementById("Tuesday").addEventListener("click", toggleButton);
document.getElementById("Wednesday").addEventListener("click", toggleButton);
document.getElementById("Thursday").addEventListener("click", toggleButton);
document.getElementById("Friday").addEventListener("click", toggleButton);
document.getElementById("Saturday").addEventListener("click", toggleButton);
document.getElementById("Sunday").addEventListener("click", toggleButton);


function toggleButton(event) {
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


document.getElementById('SelectByDistrictButton').addEventListener('click', SelectByButtonClicked);
document.getElementById('SelectByZipCodeButton').addEventListener('click', SelectByButtonClicked);
function SelectByButtonClicked(event) {
    const ClickedButton = event.target;
    const IsActive = ClickedButton.classList.contains('active');
    console.log(IsActive);
    document.getElementById('SelectByZipCodeButton').classList.remove('active');
    document.getElementById('SelectByZipCodeButton').textContent = "Select Zipcode (WIP)";
    document.getElementById('SelectByDistrictButton').classList.remove('active');
    document.getElementById('SelectByDistrictButton').textContent = "Select District (WIP)";
    SelectionOverlay.clearLayers();
    if (!IsActive) {
        ClickedButton.classList.add('active');
        ClickedButton.textContent = "Cancel";
        if (ClickedButton.id == "SelectByDistrictButton") {
            PlotDistricts(SelectionOverlay);
        }
        if (ClickedButton.id == "SelectByZipCodeButton") {
            PlotZipCodes(SelectionOverlay);
        }
    }
}


var PDColorApply = false;
document.getElementById("ColorCheckPD").addEventListener("change", function () { // Update ID to match the HTML
    if (this.checked) {
        PDColorApply = true;
        document.getElementById("ColorCheckCallDensity").checked = false; // Update ID to match the HTML
        CallDensityColorApply = false;
    } else {
        PDColorApply = false;
    }
});

var CallDensityColorApply = true;
document.getElementById("ColorCheckCallDensity").addEventListener("change", function () { // Update ID to match the HTML
    if (this.checked) {
        CallDensityColorApply = true;
        document.getElementById("ColorCheckPD").checked = false; // Update ID to match the HTML
        PDColorApply = false;
    } else {
        CallDensityColorApply = false;
    }
});


var map = L.map('map', { preferCanvas: true }).setView([43.0389, -87.9065], 10);

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
}).addTo(map);

var DisplayedRecords = L.layerGroup().addTo(map);
var BackgroundOverlay = L.layerGroup().addTo(map);
var SelectionOverlay = L.layerGroup().addTo(map);


var filteredData = [];

let CallDensityScaling = 0;

function UpdateConstants() {
    return fetch('/data') // fetch data from Flask and return the promise
        .then(response => response.json()) // parse response as JSON
        .then(data => {
            const CallDensityColumn = data.map(record => parseFloat(record[12]));
            CallDensityScaling = 1 / Math.max(...CallDensityColumn);
            console.log(`The Call Density Scaling is: ${CallDensityScaling}`);
        })
        .catch(error => console.error(error)); // handle errors
}

//Initialize
ApplyFilters();
document.getElementById('ColorCheckCallDensity').checked = true; // Update ID to match the HTML
PlotRelPoints();


document.getElementById("ClearOverlays").addEventListener("click", ClearOverlay);
function ClearOverlay() {
    BackgroundOverlay.clearLayers();
}

var CheckboxShotSpotter = document.getElementById("CallTypeFilterShotSpotter");
var CheckboxPassive = document.getElementById("CallTypeFilterPassive");
var CheckboxNVC = document.getElementById("CallTypeFilterNVC");
var CheckboxVC = document.getElementById("CallTypeFilterVC");
var CheckboxOther = document.getElementById("CallTypeFilterOther");

var MinTime = 0; // TODO CHANGE WHEN BINS DONE
var MaxTime = 24;
TODslider.noUiSlider.on('update', function (values) {
    MinTime = values[0];
    MaxTime = values[1];
    console.log('Selected min value: ' + MinTime);
    console.log('Selected max value: ' + MaxTime);
});

function Filters(record) {
    return true; //TODO remove
    const CheckBoxFilters = ["SHOTSPOTTER", "PASSIVE", "NVC", "VC", "OTHER"];
    var CheckBoxFiltersChecked = [CheckboxShotSpotter.checked, CheckboxPassive.checked, CheckboxNVC.checked, CheckboxVC.checked, CheckboxOther.checked]
    const SelectedFilters = [];
    for (let i = 0; i < CheckBoxFilters.length; i++) {
        if (CheckBoxFiltersChecked[i]) {
            SelectedFilters.push(CheckBoxFilters[i]);
        }
    }
    const Days = ["MON", "TUES", "WED", "THUR", "FRI", "SAT", "SUN"];
    var PressedDays = document.querySelectorAll(".pressed");
    const SelectedDays = [];
    for (let i = 0; i < Days.length; i++) {
        if (PressedDays[i]) {
            SelectedDays.push(Days[i]);
        }
    }
    return (SelectedFilters.includes(record[8]) & SelectedDays.includes(record[20]) & MinTime < record[21] & MaxTime > record[21]);
}

function ApplyFilters() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            window.filteredData = data.filter(item => {
                return Filters(item)
            });
        });
}

function ColorFunction(record, CDS) {
    if (PDColorApply == true) {
        switch (record[7]) {
            case '1':
                return 'orange';
            case '2':
                return 'green';
            case '3':
                return 'blue';
            case '4':
                return 'purple';
            case '5':
                return 'brown';
            case '6':
                return 'red';
            case '7':
                return 'yellow';
            default:
                return 'white';
        }
    } else if (CallDensityColorApply == true) {
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

    if (SelectedMarker !== null) {
        SelectedMarker.setStyle({
            fillOpacity: .2
        });
    }
    SelectedMarker = e.target
    SelectedMarker.setStyle({
        fillOpacity: .7,
    });
    SelectedMarker.bringToBack();

    var ID = [];
    var NATUREOFCALL = [];
    var TIME = [];
    window.filteredData.forEach(row => {
        if (row[1] == location) {
            ID.push(row[0]);
            NATUREOFCALL.push(row[8])
            TIME.push((new Date(Date.parse(row[6]))).getHours())
        }
    })
    CreateSelectedDisplay(ID, NATUREOFCALL, TIME);
}

function GeoJsonClicked(e) {
    if (SelectionOverlay.hasLayer(e.target)) {
        var SelectedZipCode = e.layer.feature.properties.ZCTA5CE10
        var SelectedDistrict = e.layer.feature.properties.POLICE
        console.log("Selected Zipcode:" + SelectedZipCode);
        console.log("Selected District:" + SelectedDistrict);
        var ID = [];
        var NATUREOFCALL = [];
        var TIME = [];
        if (SelectedZipCode !== undefined) {
            window.filteredData.forEach(row => {
                if (row[15] == SelectedZipCode) {
                    ID.push(row[0]);
                    NATUREOFCALL.push(row[8])
                    TIME.push((new Date(Date.parse(row[6]))).getHours())
                }
            })
            document.getElementById('SelectByZipCodeButton').click();
        }
        if (SelectedDistrict !== undefined) {
            window.filteredData.forEach(row => {
                if (row[11] == SelectedDistrict) {
                    ID.push(row[0]);
                    NATUREOFCALL.push(row[8])
                    TIME.push((new Date(Date.parse(row[6]))).getHours())
                }
            })
            document.getElementById('SelectByDistrictButton').click();
        }
        CreateSelectedDisplay(ID, NATUREOFCALL, TIME);
    }
};

function CreateSelectedDisplay(ID, NATUREOFCALL, TIME) {
    //SELECTED BARGRAPH
    var NATUREOFCALLCounts = {};
    NATUREOFCALL.forEach(function (NOC) {
        if (NOC in NATUREOFCALLCounts) {
            NATUREOFCALLCounts[NOC]++;
        } else {
            NATUREOFCALLCounts[NOC] = 1;
        }
    });

    var Trace = {
        x: Array.from(new Set(NATUREOFCALL)),
        y: Object.values(NATUREOFCALLCounts),
        type: 'bar',
        orientation: 'v'
    };
    var Data = [Trace];
    var Layout = {
        title: 'Bargraph at Selection',
        margin: { t: 30 },
        xaxis: { title: 'Nature of Call' },
        yaxis: { title: 'Count' }
    };
    Plotly.newPlot('SelectedCallsPlot', Data, Layout, { displayModeBar: false });

    //SELECTED TIME HIST

    var TickVals = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5];
    var TickText = ['12:00 am', '1:00 am', '2:00 am', '3:00 am', '4:00 am', '5:00 am', '6:00 am', '7:00 am', '8:00 am', '9:00 am', '10:00 am', '11:00 am', '12:00 pm', '1:00 pm', '2:00 pm', '3:00 pm', '4:00 pm', '5:00 pm', '6:00 pm', '7:00 pm', '8:00 pm', '9:00 pm', '10:00 pm', '11:00 pm'];
    var TraceTime = {
        x: TIME,
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
        title: { text: 'Time of Call', font: { size: 15 } },
        margin: { t: 30 },
        bargap: 0.05,
        xaxis: {
            title: 'Time',
            margin: { t: 20 },
            range: [0, 24],
            dtick: 1,
            tickmode: 'array',
            tickvals: TickVals,
            ticktext: TickText,
            tickangle: 90
        },
        hovermode: 'closest',
        yaxis: {
            title: '',
            nticks: 2
        },
        height: 150
    };
    Plotly.newPlot('SelectedCallsTimeHist', DataTime, LayoutTime, { displayModeBar: false });
}


function PlotRelPoints() {
    ApplyFilters();
    DisplayedRecords.clearLayers();
    var PlottedLocations = {};
    UpdateConstants().then(() => {
        console.log(`Call Density Scaling: ${CallDensityScaling}`);
        const locationCounts = {};
        window.filteredData.filter(row => row[14] == 0).forEach(row => {
            const location = row[1];
            locationCounts[location] = (locationCounts[location] || 0) + 1;
        });
        window.filteredData.filter(row => row[14] == 0).forEach(row => {
            const location = row[1];
            if (!PlottedLocations[location]) {
                PlottedLocations[location] = true;
                const radius = 10 + (locationCounts[location] ** .5) * 10;
                const markerCOS = L.circle([row[2], row[3]],
                    {
                        stroke: true,
                        opacity: .6,
                        weight: 2,
                        color: chroma(ColorFunction(row, CallDensityScaling)).darken().hex(),
                        fillOpacity: .2,
                        fillColor: ColorFunction(row, CallDensityScaling)
                    }).setRadius(radius).addTo(DisplayedRecords).on('click', MakerClicked);
                markerCOS.LocationData = location;
                markerCOS.bindPopup(row[1]);
            }
        });
        window.filteredData.forEach(row => {
            if ((row[14] != 0)) {
                const location = row[1];
                if (!PlottedLocations[location]) {
                    PlottedLocations[location] = true;
                    const adminLocations = L.canvasMarker(L.latLng(row[2], row[3]),
                        {
                            img: {
                                url: '/static/star-filled.png',
                                size: [20, 20],     //image size ( default [40, 40] )
                                //rotate: 10,         //image base rotate ( default 0 )
                                //offset: { x: 0, y: 0 }, //image offset ( default { x: 0, y: 0 } )
                            },
                        }).addTo(DisplayedRecords).on('click', MakerClicked);
                        adminLocations.LocationData = location;
                        adminLocations.bindPopup(row[1]);
                }
            }
        });
    });
}


document.getElementById("PlotDistricts").addEventListener("click", function () { PlotDistricts(BackgroundOverlay) });
document.getElementById("PlotZIPCODE").addEventListener("click", function () { PlotZipCodes(BackgroundOverlay) });

function PlotDistricts(TargetLayer) {
    console.log("Plotting Districts");
    fetch('/geojson')
        .then(response => response.json())
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
                }
            }).addTo(TargetLayer).on('click', GeoJsonClicked);
        })
}

function PlotZipCodes(TargetLayer) {
    console.log("Plotting Zipcodes");
    fetch('/geojsonZIPCODES')
        .then(response => response.json())
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
                    layer.bindPopup('Zipcode: ' + feature.properties.ZCTA5CE10);
                }
            }).addTo(TargetLayer).on('click', GeoJsonClicked);
        })
}


function PlotBars() {
    fetch('/bars')
        .then(response => response.json())
        .then(geojson => {
            L.geoJSON(geojson, {
                pointToLayer: function (feature, latlng) {
                    return L.canvasMarker(L.latLng(latlng), {
                        img: {
                            url: '/static/baricon.png',
                            size: [10, 10],
                        }
                    })
                },
                onEachFeature: function (feature, layer) {
                    layer.bindPopup('Bar: ' + feature.properties.name);
                }
            }).addTo(DisplayedRecords);
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



