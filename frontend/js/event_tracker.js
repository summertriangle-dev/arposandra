import Infra from "./infra"
import React from "react"
import ReactDOM from "react-dom"
import {connect, Provider} from "react-redux"
import { SaintDatasetCoordinator, SaintUserConfig, toRankTypeFriendlyName, 
    rankTypesForEventType, localizeDatasetName, compareDatasetKey } from "./event_tracker_internal"

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
                    return <a key={v} className={this.isSelected(v)} 
                        onClick={() => this.props.setMode(this.props.eventType, v)}>
                        {toRankTypeFriendlyName(v)}
                    </a>
                })}
            </div>
            <button className="btn btn-sm btn-primary"
                onClick={() => this.props.enterEditMode()}>{this.props.editMode? 
                    Infra.strings.Saint.ExitEditMode :
                    Infra.strings.Saint.EnterEditMode}</button>
        </div>
    }
}

const SaintRankTypeSelector = connect(
    (state) => { return {rankMode: state.saint.rankMode, editMode: state.saint.editMode} },
    (dispatch) => {
        return {
            setMode: (t, m) => dispatch({
                type: `${SaintUserConfig.actions.setMode}`, 
                mode: m, 
                forType: t
            }),
            enterEditMode: () => dispatch({
                type: `${SaintUserConfig.actions.enterEditMode}`
            })
        }
    })(_SaintRankTypeSelector)

function SaintDisplayBoardCard(props) {
    let diff2sym
    if (!props.datum.delta2) {
        diff2sym = "-"
    } else if (props.datum.delta2 > 0) {
        diff2sym = <span 
            title={Infra.strings.formatString(Infra.strings.Saint.TrendingUp, props.datum.delta2)} 
            className="small text-success">↑</span>
    } else {
        diff2sym = <span 
            title={Infra.strings.formatString(Infra.strings.Saint.TrendingDown, props.datum.delta2)} 
            className="small text-danger">↓</span>
    }

    return <div className="card kars-event-cutoff-card">
        <div className="card-body">
            <p className="card-text mb-1">{props.datum.label}</p>
            <p className="h5 card-title mb-1">
                {Infra.strings.formatString(Infra.strings.Saint.PointCount, props.datum.points)}</p>
            <p className="h6 card-subtitle my-0">
                {diff2sym}
                {" "}
                <span className="delta-word">{props.datum.delta || "--"}</span>
            </p>
        </div>
    </div>
}

const SaintDisplayBoard = connect(
    (state) => {
        return {
            rankMode: state.saint.rankMode,
            displayTiers: state.saint.displayTiers
        }
    }
)(function(props) {
    const prefix = `${props.rankMode[props.eventType]}.`
    const vset = Object.keys(props.displayTiers[props.eventType]).filter((v) => {
        return v.startsWith(prefix) && props.displayTiers[props.eventType][v]
    })

    vset.sort(compareDatasetKey)
    return <div className="row">
        {vset.map((k) => {
            const s = props.summaryData[k]
            if (!s) {
                return null
            }
            return <div className="col-sm-4" key={k}>
                <SaintDisplayBoardCard datum={s} />
            </div>
        })}
    </div>
})

class _SaintDisplayEditor extends React.Component {
    buttonsToShow() {
        const prefix = `${this.props.rankMode[this.props.eventType]}.`
        let show = []
        for (let key of this.props.available) {
            if (key.startsWith(prefix)) show.push(key)
        }

        return show.sort(compareDatasetKey)
    }

    render() {
        const map = this.props.displayTiers[this.props.eventType]

        return <div className="row">
            {this.buttonsToShow().map((k) => {
                return <div className="col-md-4" key={k}>
                    <div className="card kars-event-cutoff-card" 
                        onClick={() => this.props.toggleVisSet(this.props.eventType, k)}>
                        <div className="card-body">
                            <p className="card-text h6">
                                {localizeDatasetName(k)} {" "}
                                <input type="checkbox" 
                                    checked={map[k] === true} 
                                    readOnly={true}
                                    style={{float: "right"}} />
                            </p>
                        </div>
                    </div>
                </div>
            })}
        </div>
    }
}
const SaintDisplayEditor = connect((state) => { return {
    rankMode: state.saint.rankMode,
    displayTiers: state.saint.displayTiers,
}}, (dispatch) => { return {
    toggleVisSet: (m, k) => dispatch({
        type: `${SaintUserConfig.actions.toggleVisFlag}`,
        forType: m,
        key: k
    })
}})(_SaintDisplayEditor)

const SaintRoot = connect((state) => { return {editMode: state.saint.editMode} })(
    function(props) {
        const pad2 = (n) => n < 10? "0" + n : n
        const checkin = `${pad2(props.lastCheckin.getHours())}:${pad2(props.lastCheckin.getMinutes())}`
        const update = `${pad2(props.lastUpdate.getHours())}:${pad2(props.lastUpdate.getMinutes())}`

        return <div>
            <h2 className="h4 mb-2">{Infra.strings.Saint.HeaderCurrentTiers}</h2>
            <SaintRankTypeSelector eventType={props.eventType} />
            {props.editMode?
                <SaintDisplayEditor eventType={props.eventType} available={props.availableSet}/> :
                <SaintDisplayBoard eventType={props.eventType} summaryData={props.summaries} /> }
            <p className="small mb-0 mt-3">
                {Infra.strings.Saint.UpdateTimeNote}{" "}
                {Infra.strings.formatString(Infra.strings.Saint.UpdateTime, checkin, update)}
            </p>
        </div>
    }
)

class SaintDisplayController {
    constructor(canvas) {
        this.canvas = canvas
        this.chartData = new SaintDatasetCoordinator(canvas.dataset.serverId, 
            parseInt(canvas.dataset.eventId))
        this.chart = null
        this.timeout = null
        this.eventType = canvas.dataset.eventType

        Infra.store.dispatch({type: `${SaintUserConfig.actions.loadFromLocalStorage}`})
        Infra.store.subscribe(() => {
            if (Infra.canWritebackState()) {
                const {displayTiers, rankMode} = Infra.store.getState().saint
                localStorage.setItem("as$$saint", JSON.stringify({displayTiers, rankMode}))
            }
            this.updateReact()
        })
    }

    install() {
        this.installTimer()
        this.updateReact()
    }

    installTimer() {
        this.timeout = setInterval(() => this.refreshData(), 15*60*1000)
    }

    disableUpdates() {
        if (this.timeout) {
            clearInterval(this.timeout)
        }
    }

    refreshData() {
        this.chartData.refresh().then(() => {
            console.log(this.chartData)
            this.updateReact()
        })
    }

    updateReact() {
        const set = Object.keys(this.chartData.datasets).sort()
        const summaries = this.chartData.summaryForDatasets(set)
        ReactDOM.render(<Provider store={Infra.store}>
            <SaintRoot 
                availableSet={set}
                eventType={this.eventType}
                summaries={summaries}
                lastCheckin={new Date(this.chartData.lastCheckinTime * 1000)}
                lastUpdate={new Date(this.chartData.lastUpdateTime * 1000)} />
        </Provider>, this.canvas)
    }
}
  
let controller

export function injectIntoPage() {
    const tgt = document.getElementById("saint-inject-target")
    controller = new SaintDisplayController(tgt)
    controller.install()
    controller.refreshData()
}