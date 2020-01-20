import Infra from "./infra"
import React from "react"
import ReactDOM from "react-dom"
import { SaintDatasetCoordinator, toRankTypeFriendlyName } from "./event_tracker_internal"

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

const THEME_VARS = {
    dark: {
        gridLines: "rgba(238, 238, 238, 0.1)",
        textColor: "#eeeeee",
    },
    light: {
        gridLines: "rgba(51, 51, 51, 0.1)",
        textColor: "#333333",
    }
}

function colourArray(n) {
    let a = new Array(n)
    for (let i = 0; i < n; ++i) {
        a[i] = COLOURS[i % COLOURS.length]
    }
    return a
}

class SaintDisplayBoard extends React.Component {
    render() {
        return <ul>
            {this.props.visibility.map((k) => {
                const s = this.props.summaryData[k]
                if (!s) {
                    return null
                }
                return <li key={k}>Pts: {s.points} Delta: {s.delta} Diff2: {s.delta2}</li>
            })}
        </ul>
    }
}

class SaintDisplayController {
    constructor(canvas) {
        this.canvas = canvas
        this.displayStat = "points"
        this.chartData = new SaintDatasetCoordinator(canvas.dataset.serverId, 
            parseInt(canvas.dataset.eventId))
        this.chart = null
        this.timeout = null
        this.visibleSet = DEFAULT_DATASETS_TO_SHOW
    }

    didFireRefreshTimer() {
        this.chartData.refresh().then(() => {
            console.log(this.chartData)
            this.installDisplayBoard()
        })
    }

    installTimer() {
        this.timeout = setInterval(() => this.didFireRefreshTimer(), 15 * 60 * 1000)
    }

    disableUpdates() {
        if (this.timeout) {
            clearInterval(this.timeout)
        }
    }

    didSelectRankingType(rankType) {
        this.displayStat = rankType
        this.refreshData()
    }

    shouldDatasetBeVisible(theSet) {
        if (theSet.rankType === this.displayStat) {
            return true
        }
        return false
    }

    refreshData() {
        this.chartData.refresh().then(() => {
            console.log(this.chartData)
            this.installDisplayBoard()
        })
    }

    installDisplayBoard() {
        const summaries = this.chartData.summaryForDatasets(Object.keys(this.chartData.datasets))
        ReactDOM.render(<SaintDisplayBoard visibility={this.visibleSet} summaryData={summaries} />, this.canvas.querySelector("#saintCutoffBoard"))
    }
}

function initRankSwitch(rs, forController) {
    let rankTypes
    switch(rs.dataset.eventType) {
    case "mining":
        rankTypes = ["points", "voltage"]
        break
    default:
        rankTypes = null
        break
    }

    if (!rankTypes) return

    const label = document.createElement("span")
    label.className = "item"
    label.textContent = Infra.strings.Saint.RankTypeSwitchLabel
    rs.appendChild(label)

    const sw = document.createElement("div")
    sw.className = "item kars-image-switch always-active"
    rs.appendChild(sw)

    const didSelectSwitch = (event) => {
        const rankType = event.target.dataset.target
        forController.didSelectRankingType(rankType)

        const buttons = sw.querySelectorAll("a")
        for (let i = 0; i < buttons.length; ++i) {
            buttons[i].className = ""
        }
        event.target.className = "selected"
    }

    for (let i = 0; i < rankTypes.length; ++i) {
        const knob = document.createElement("a")
        knob.className = (i == 0)? "selected" : ""
        knob.textContent = toRankTypeFriendlyName(rankTypes[i])
        knob.dataset.target = rankTypes[i]
        knob.addEventListener("click", didSelectSwitch, {passive: true})
        sw.appendChild(knob)
    }
}
  
let controller

export function injectIntoPage() {
    controller = new SaintDisplayController(document.getElementById("saintControl"))
    const rankSwitch = document.getElementById("saintRankTypeSelector")
    initRankSwitch(rankSwitch, controller)

    controller.refreshData()
    controller.installTimer()
    controller.installDisplayBoard()
}