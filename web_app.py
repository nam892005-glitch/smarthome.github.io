<!DOCTYPE html>
<html>
<head>
    <title>SmartHome</title>
</head>
<body>
    <h1>SmartHome Control</h1>

    <button onclick="openDoor()">Mở cửa</button>
    <button onclick="lightOn()">Bật đèn</button>
    <button onclick="lightOff()">Tắt đèn</button>

    <h2 id="status">Status: --</h2>

<script>
const API = "https://your-render-url.onrender.com"; // THAY LINK

function openDoor(){
    fetch(API + "/door", {method:"POST"});
}

function lightOn(){
    fetch(API + "/light", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({state:"ON"})
    });
}

function lightOff(){
    fetch(API + "/light", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({state:"OFF"})
    });
}

function getStatus(){
    fetch(API + "/status")
    .then(res => res.json())
    .then(data => {
        document.getElementById("status").innerText =
            "Status: " + data.result;
    });
}

setInterval(getStatus, 2000);
</script>

</body>
</html>
