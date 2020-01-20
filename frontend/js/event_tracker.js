import Infra from "./infra"
import React from "react"
import ReactDOM from "react-dom"
import {connect, Provider} from "react-redux"
import { SaintDatasetCoordinator, SaintUserConfig, toRankTypeFriendlyName, rankTypesForEventType } from "./event_tracker_internal"

const DEFAULT_DATASETS_TO_SHOW = [
    "points.50000",
    "points.40000",
    "points.10000",
    "points.1000"
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

class _SaintRankTypeSelector extends React.Component {
    isSelected(m) {
        return this.props.rankMode[this.props.eventType] === m? "selected" : null
    }

    render() {
        const choices = rankTypesForEventType(this.props.eventType)
        if (choices.length < 2) {
            return <div></div>
        }

        return <div className="kars-sub-navbar is-left">
            <span className="item">{Infra.strings.Saint.RankTypeSwitchLabel}</span>
            <div className="item kars-image-switch always-active">
                {choices.map((v) => {
                    return <a className={this.isSelected(v)} 
                        onClick={() => this.props.setMode(this.props.eventType, v)}>
                        {toRankTypeFriendlyName(v)}
                    </a>
                })}
            </div>
        </div>
    }
}

const SaintRankTypeSelector = connect(
    (state) => { return {rankMode: state.saint.rankMode} },
    (dispatch) => {
        return {
            setMode: (t, m) => dispatch({type: `${SaintUserConfig.actions.setMode}`, 
                mode: m, forType: t})
        }
    })(_SaintRankTypeSelector)

function SaintDisplayBoardCard(props) {
    let sym
    if (!props.d.delta) {
        sym = "-"
    } else if (props.d.delta > 0) {
        sym = "↑"
    } else {
        sym = "↓"
    }

    let diff2sym
    if (!props.d.diff2) {
        diff2sym = "-"
    } else if (props.d.diff2 > 0) {
        diff2sym = "↑"
    } else {
        diff2sym = "↓"
    }

    return <div className="card">
        <div className="card-body">
            <p className="card-text my-0">{props.d.points}</p>
            <p className="card-subtitle my-0">
                <span className="delta-symbol">{sym}</span>
                {" "}
                <span className="delta-symbol small">{diff2sym}</span>
                {" "}
                <span className="delta-word">{props.d.delta || "--"}</span>
            </p>
        </div>
    </div>
}

function SaintDisplayBoard(props) {
    return <div className="row">
        {props.visibility.map((k) => {
            const s = props.summaryData[k]
            if (!s) {
                return null
            }
            return <div className="col-4" key={k}><SaintDisplayBoardCard d={s} /></div>
        })}
    </div>
}

class SaintDisplayController {
    constructor(canvas) {
        this.canvas = canvas
        this.chartData = new SaintDatasetCoordinator(canvas.dataset.serverId, 
            parseInt(canvas.dataset.eventId))
        this.chart = null
        this.timeout = null

        Infra.store.dispatch({type: `${SaintUserConfig.actions.loadFromLocalStorage}`})
        Infra.store.subscribe(() => {
            if (Infra.canWritebackState()) {
                localStorage.setItem("as$$saint", JSON.stringify(state.saint))
            }
        })
    }

    installTimer() {
        this.timeout = setInterval(() => this.refreshData(), 15 * 60 * 1000)
    }

    disableUpdates() {
        if (this.timeout) {
            clearInterval(this.timeout)
        }
    }

    refreshData() {
        this.chartData.refresh().then(() => {
            console.log(this.chartData)
            this.installDisplayBoard()
        })
    }

    installDisplayBoard() {
        const et = document.querySelector("#saintRankTypeSelector").dataset.eventType
        const summaries = this.chartData.summaryForDatasets(Object.keys(this.chartData.datasets))
        ReactDOM.render(<SaintDisplayBoard visibility={Infra.store.getState().saint.displayTiers} summaryData={summaries} />, this.canvas.querySelector("#saintCutoffBoard"))
        ReactDOM.render(<Provider store={Infra.store}><SaintRankTypeSelector eventType={et} /></Provider>, this.canvas.querySelector("#saintRankTypeSelector"))
    }
}
  
let controller

export function injectIntoPage() {
    controller = new SaintDisplayController(document.getElementById("saintControl"))
    controller.refreshData()
    controller.installTimer()
    controller.installDisplayBoard()
}