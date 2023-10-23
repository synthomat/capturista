document.addEventListener("DOMContentLoaded", () => {
    document.body.addEventListener('htmx:configRequest', function (evt) {
        evt.detail.headers['X-CSRFToken'] = csrf_token;
    })
})

function request(url, options) {
    return fetch(url, {
            ...options,
            headers: {
                ...((options !== undefined) ? options.headers : {}),
                'X-CSRFToken': csrf_token
            }
        }
    )
}


function triggerData() {
    request("/api/states")
        .then(r => r.json())
        .then(j => {
            Alpine.store('sources').setData(j.instances).then(() => {
                htmx.process(document.body)
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
})

function startWatch() {
    window.addEventListener("load", (e) => {
        setInterval(triggerData, 2000);
        triggerData()
    })
}


