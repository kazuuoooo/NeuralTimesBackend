async function getQueue() {
    const response = await fetch('http://localhost:5000/queue');
    const data = await response.json();
    document.getElementById('queue').innerHTML = JSON.stringify(data, null, 2);
}


async function addToQueue(event) {
    event.preventDefault();
    const topicinformation = document.getElementById('topicinformation').value;
    const sources = document.getElementById('sources').value;
    await fetch('http://localhost:5000/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topicinformation,
            sources
        })
    });
    getQueue();
}



async function startJob() {
    await fetch('http://localhost:5000/start-job', {method: 'POST'});
}

window.onload = function() {
    getQueue();
    document.getElementById('add-to-queue-form').addEventListener('submit', addToQueue);
    document.getElementById('start-job').addEventListener('click', startJob);
};