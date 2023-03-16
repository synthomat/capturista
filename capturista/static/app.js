function triggerData() {
    fetch("/api/states")
        .then(r => r.json())
        .then(j => {
            document.getElementById("queue-size").textContent = j.queue_length

            Alpine.store('sources').setData(j.instances).then(() => {
                // htmx.process(document.body)
            })
        })
}


document.addEventListener('alpine:init', () => {
    Alpine.store('sources', {
        data: [],

        setData(d) {
            this.data = d
            return new Promise(resolve => resolve(d))
        }
    })

    setInterval(triggerData, 2000);
    triggerData()
})

window.addEventListener("load", (e) => {
})

