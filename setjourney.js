const sideMenu = document.querySelector("aside");
const profileBtn = document.querySelector("#profile-btn");
const themeToggler = document.querySelector(".theme-toggler");
const nextDay = document.getElementById('nextDay');
const prevDay = document.getElementById('prevDay');

profileBtn.onclick = function() {
    sideMenu.classList.toggle('active');
}
window.onscroll = () => {
    sideMenu.classList.remove('active');
    if(window.scrollY > 0){document.querySelector('header').classList.add('active');}
    else{document.querySelector('header').classList.remove('active');}
}

themeToggler.onclick = function() {
    document.body.classList.toggle('dark-theme');
    themeToggler.querySelector('span:nth-child(1)').classList.toggle('active')
    themeToggler.querySelector('span:nth-child(2)').classList.toggle('active')
}

let setData = (day) =>{
    document.querySelector('table tbody').innerHTML = ' '; //To clear out previous table data;  
    let daylist = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    document.querySelector('.timetable div h2').innerHTML = daylist[day];
    switch(day){
        case(0): day = Sunday; break;
        case(1): day = Monday; break;
        case(2): day = Tuesday; break;
        case(3): day = Wednesday; break;
        case(4): day = Thursday; break;
        case(5): day = Friday; break;
        case(6): day = Saturday; break;
    }

    day.forEach(sub => {
        const tr = document.createElement('tr');
        const trContent = `
                            <td>${sub.time}</td>
                            <td>${sub.roomNumber}</td>
                            <td>${sub.subject}</td>
                            <td>${sub.type}</td>
                        `
        tr.innerHTML = trContent;
        document.querySelector('table tbody').appendChild(tr)                        
    });
}

let now = new Date();
let today = now.getDay(); // Will return the present day in numerical value; 
let day = today; //To prevent the today value from changing;

function timeTableAll(){
    document.getElementById('timetable').classList.toggle('active');
    setData(today);
    document.querySelector('.timetable div h2').innerHTML = "Today's Timetable";
}
nextDay.onclick = function() {
    day<=5 ? day++ : day=0;  // If else one liner
    setData(day);
}
prevDay.onclick = function() {
    day>=1 ? day-- : day=6;    
    setData(day);
}

setData(day); //To set the data in the table on loading window.
document.querySelector('.timetable div h2').innerHTML = "Today's Timetable"; //To prevent overwriting the heading on loading;

const map = L.map('map').setView([28.6950, 77.0880], 12); // Centered around Narela and Rithala

// Add OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, // Set a reasonable maximum zoom level
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Add a starting marker for Narela
const marker1 = L.marker([28.7070, 77.0673]).addTo(map); // Narela
marker1.bindPopup('Narela').openPopup();

// Add a destination marker for Rithala
const marker2 = L.marker([28.6831, 77.1068]).addTo(map); // Rithala
marker2.bindPopup('Rithala').openPopup();

// Create a line between the two points
const latlngs = [
    [28.7070, 77.0673], // Narela
    [28.6831, 77.1068]  // Rithala
];
const polyline = L.polyline(latlngs, { color: 'blue' }).addTo(map);

// Fit the map to show both markers
map.fitBounds(polyline.getBounds());
