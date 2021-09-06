var duration_ms_txt = document.getElementById("duration_ms");
var rpm_txt = document.getElementById("rpm");
var rpm_lbl = document.getElementById("rpm_lbl");
var start_btn = document.getElementById("start-btn");
var running = false;


async function do_post(url, body, callback) {
    await fetch(
        window.location.protocol + "//" + window.location.host + url,
        {
            method: 'POST',
            body: JSON.stringify(body)
        }
    ).then(callback);
}

async function fetch_values() {
    await fetch(window.location.protocol + "//" + window.location.host + '/api/spinner')
        .then(response => response.json())
        .then(json => {
            rpm_lbl.innerText = "Current RPM: " + Math.round(json.rpm);

            if (json.estop) {
                start_btn.innerText = "Emergency Stop";
                start_btn.classList.add("stop-btn");
            } else if (!running) {
                start_btn.innerText = "Begin LERP";
                start_btn.classList.remove("stop-btn");
            }
        });
}

function on_click() {
    if (running) {
        do_post(
            '/api/spinner/estop',
            {
                'estop': true,
            },
            () => { }
        )
        return;
    }

    start_btn.innerText = "Emergency Stop";
    start_btn.classList.add("stop-btn");
    running = true;

    do_post(
        '/api/spinner/lerp',
        {
            'duration_ms': Number(duration_ms_txt.value),
            'rpm': Number(rpm_txt.value),
        },
        () => {
            running = false;
            start_btn.innerText = "Begin LERP";
            start_btn.classList.remove("stop-btn");
        }
    )
}


start_btn.addEventListener("click", on_click);

setInterval(fetch_values, 100);
