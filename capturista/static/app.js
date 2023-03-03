window.addEventListener("load", (e) => {
    setInterval(() => {
        fetch("/api/states")
            .then(r => r.json())
            .then(j => {
                document.getElementById("queue-size").textContent = j.queue_length

                let instances = j.instances

                instances.forEach(cfg => {
                    document.querySelector('tr[data-cid="' + cfg.id + '"] .status').textContent = cfg.status
                    document.querySelector('tr[data-cid="' + cfg.id + '"] .last-run').textContent = cfg.last_run
                })
            })
    }, 2000);
})