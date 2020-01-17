import Infra from "./infra"

let chartjs
let chartData

const DEFAULT_DATASETS_TO_SHOW = [
    "points.50000",
    "points.40000",
    "points.10000",
]

const COLOURS = [
    "#007bff",
    "#6610f2",
    "#e83e8c",
    "#dc3545",
    "#fd7e14",
    "#ffc107",
    "#28a745",
    "#20c997",
]

function colourArray(n) {
    let a = new Array(n)
    for (let i = 0; i < n; ++i) {
        a[i] = COLOURS[i % COLOURS.length]
    }
    return a
}

function localizeDatasetName(dsn) {
    let s = dsn.split(".")
    if (s.length !== 2) return s

    let criteria
    switch(s[0]) {
    case "voltage": criteria = Infra.strings.Saint.DatasetFriendlyName.Voltage; break
    case "points": criteria = Infra.strings.Saint.DatasetFriendlyName.Points; break
    default: criteria = s[0]; break
    }

    return Infra.strings.formatString(Infra.strings.Saint.DatasetNameFormat, s[1], criteria)
}

class SaintDatasetCoordinator {
    constructor(serverid, eventID) {
        this.serverid = serverid
        this.eventId = eventID
        this.lastCheckTime = 0
        this.status = 0
        this.lastError = null

        this.datasets = {}
    }

    async refresh() {
        const nextLastTime = (Date.now() / 1000) | 0
        const adata = await this.getUpdateFromAPI(this.lastCheckTime)

        if (!adata.result) {
            this.status = 0
            this.lastError = adata.error? adata.error : "Unknown server error"
            return
        }

        const R = adata.result
        this.lastCheckTime = nextLastTime
        if (R.is_new) {
            const keys = Object.keys(R.datasets)
            const colours = colourArray(keys.length)
            this.datasets = {}
            keys.map((k, i) => {
                return {
                    _saintRealName: k,
                    label: localizeDatasetName(k),
                    data: SaintDatasetCoordinator.reshapeDataset(R.datasets[k]),
                    fill: false,
                    borderWidth: 2,
                    borderColor: colours[i]
                }
            }).forEach((v) => this.datasets[v.label] = v)
        } else {
            for (let dataset of Object.keys(adata.result.datasets)) {
                const se = this.datasets[dataset]
                se.data.push(
                    ...SaintDatasetCoordinator.reshapeDataset(R.datasets[dataset]))
                if (se.length > 50) {
                    se.splice(0, se.length - 50)
                }
            }

        }
    }

    static reshapeDataset(dso) {
        return dso.map((v) => {return {y: v[1], t: v[0]}})
    }

    getUpdateURL() {
        return `/api/private/saint/${this.serverid}/${this.eventId}/tiers.json`
    }

    async getUpdateFromAPI(last) {
        const xhr = new XMLHttpRequest()
        return new Promise((resolve, reject) => {
            xhr.onreadystatechange = () => {
                if (xhr.readyState !== 4) return
    
                if (xhr.status == 200) {
                    const json = JSON.parse(xhr.responseText)
                    resolve(json)
                } else {
                    reject()
                }
            }
            xhr.open("GET", `${this.getUpdateURL()}?after=${last}`)
            xhr.send()
        })
    }
}

class SaintTop10DatasetCoordinator extends SaintDatasetCoordinator {
    getUpdateURL() {
        return `/api/private/saint/${this.serverid}/${this.eventId}/top10.json`
    }
}

function initSaintAfterChartsReady() {
    const sg = document.getElementById("saintGraph")
    chartData = new SaintDatasetCoordinator(sg.dataset.serverId, parseInt(sg.dataset.eventId))
    
    let ctx = sg.getContext("2d")
    let myChart = new chartjs.Chart(ctx, {
        type: "line",
        data: {
            labels: [
                new Date(2019,12,31,12,0,0), 
                new Date(2019,12,31,13,0,0), 
                new Date(2019,12,31,14,0,0), 
                new Date(2019,12,31,15,0,0),
                new Date(2019,12,31,16,0,0),
                new Date(2019,12,31,17,0,0),
            ],
            datasets: [{
                label: "Points",
                data: [12, 19, 3, 5, 2, 3],
                fill: false,
                borderWidth: 2
            }]
        },
        options: {
            animation: {duration: 0}, // general animation time
            hover: {animationDuration: 0}, // duration of animations when hovering an item
            responsiveAnimationDuration: 0, // animation duration after a resize
            elements: {
                line: {
                    tension: 0 // disables bezier curves
                }
            },
            scales: {
                xAxes: [{
                    type: "time",
                    time: {
                        unit: "hour"
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
    })

    chartData.refresh().then(() => {
        console.log(chartData)
        let ds = []
        for (let name of Object.keys(chartData.datasets)) {
            ds.push(chartData.datasets[name])
            if (DEFAULT_DATASETS_TO_SHOW.indexOf(chartData.datasets[name]._saintRealName) == -1) {
                chartData.datasets[name].hidden = true
            }
        }

        myChart.data.labels = chartData.xAxis
        myChart.data.datasets = ds
        myChart.update()
    })

}

export function injectIntoPage() {
    import("chart.js").then((_chartjs) => {
        chartjs = _chartjs
        initSaintAfterChartsReady()
    })
}