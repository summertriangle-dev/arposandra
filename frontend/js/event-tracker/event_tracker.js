import Infra from "../infra"
import React from "react"
import ReactDOM from "react-dom"
import Chart from "chart.js"
import {connect, Provider, useSelector} from "react-redux"
import { SaintDatasetCoordinator, SaintT10DatasetCoordinator, SaintUserConfig, toRankTypeFriendlyName, 
    rankTypesForEventType, compareDatasetKey } from "./event_tracker_internal"
import { MultiValueSwitch } from "../ui_lib"
import { effectiveAppearance } from "../appearance"
import { hasStoragePermission, requestStoragePermission } from "../storage_permission"

const hslBase = (h, s, baseL) =>
    (itr) => `hsl(${h}, ${s}%, ${baseL + (5 * itr)}%)`

const COLOURS = [
    hslBase(0, 84, 64),
    hslBase(30, 80, 60),
    hslBase(47, 87, 51),
    hslBase(138, 43, 51),
    hslBase(180, 69, 40),
    hslBase(197, 61, 46),
    hslBase(224, 68, 50),
    hslBase(287, 29, 50),
]

function arraySame(a, b) {
    if (a.length !== b.length) {
        return false
    }

    for (let i = 0; i < a.length; ++i) {
        if (a[i] != b[i]) {
            return false
        }
    }
    return true
}

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

class _SaintRankTypeSelector extends MultiValueSwitch {
    getChoices() {
        return rankTypesForEventType(this.props.eventType)
    }

    showOnlyWithChoices() {
        return false
    }

    getLabelForChoice(v) {
        return toRankTypeFriendlyName(v)
    }

    getCurrentSelection() {
        return this.props.rankMode[this.props.eventType]
    }

    changeValue(toValue) {
        this.props.setMode(this.props.eventType, toValue)
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

function symbolForDelta2(datum) {
    let diff2sym
    if (!datum.delta2) {
        diff2sym = "-"
    } else if (datum.delta2 > 0) {
        diff2sym = <span 
            title={Infra.strings.formatString(Infra.strings.Saint.TrendingUp, datum.delta2)} 
            className="small text-success">↑</span>
    } else {
        diff2sym = <span 
            title={Infra.strings.formatString(Infra.strings.Saint.TrendingDown, datum.delta2)} 
            className="small text-danger">↓</span>
    }
    return diff2sym
}

const ONE_HR_MS = 3600000
const ONE_MIN_MS = 60000
function relTime(msecs) {
    if (msecs >= 3600000) {
        return Infra.strings.formatString(Infra.strings.Saint.RTime.Hours, (msecs / ONE_HR_MS).toFixed(0))
    } else {
        return Infra.strings.formatString(Infra.strings.Saint.RTime.Minutes, (msecs / ONE_MIN_MS).toFixed(0))
    }
}

function SaintDisplayBoardCard(props) {
    return <div className="card kars-event-cutoff-card">
        <div className="card-body">
            <p className="card-text mb-1">{props.datum.label}</p>
            <p className="h5 card-title mb-1">
                {Infra.strings.formatString(Infra.strings.Saint.PointCount, props.datum.points)}
                {" "}
                <span className="h6 my-0">
                    {symbolForDelta2(props.datum)} {" "}
                    <span className="delta-word">{props.datum.delta || "--"}/{relTime(props.datum.deltaCover)}</span>
                </span>
            </p>
            
        </div>
    </div>
}

function SaintDisplayBoardCardT10(props) {
    return <div className="card kars-event-cutoff-card">
        <div className="card-body">
            <p className="card-text mb-1">{props.datum.label}: <i>{props.datum.who}</i></p>
            <p className="h5 card-title mb-1">
                {Infra.strings.formatString(Infra.strings.Saint.PointCount, props.datum.points)}
                {" "}
                <span className="h6 my-0">
                    {symbolForDelta2(props.datum)} {" "}
                    <span className="delta-word">{props.datum.delta || "--"}/{relTime(props.datum.deltaCover)}</span>
                </span>
            </p>
        </div>
    </div>
}

function SaintDisplayBoard(props) {
    const config = useSelector((state) => ({
        rankMode: state.saint.rankMode,
        displayTiers: state.saint.displayTiers
    }))
    const prefix = `${config.rankMode[props.eventType]}.`
    const vset = Object.keys(config.displayTiers[props.eventType]).filter((v) => {
        return v.startsWith(prefix) && config.displayTiers[props.eventType][v]
    })
    vset.sort(compareDatasetKey)
    const CardProp = props.trackType == "top10"? SaintDisplayBoardCardT10 : SaintDisplayBoardCard

    if (vset.length == 0) {
        return <div className="row">
            <div className="col-12">
                <div className="card kars-event-cutoff-card">
                    <div className="card-body h6 mb-0 text-center">
                        {Infra.strings.Saint.BoardNoRankingsEnabledHint}
                    </div>
                </div>
            </div>
        </div>
    }

    return <div className="row">
        {vset.map((k) => {
            const s = props.summaryData[k]
            if (!s) {
                return null
            }
            return <div className="col-sm-4" key={k}>
                <CardProp datum={s} />
            </div>
        })}
    </div>
}

class _SaintDisplayEditor extends React.Component {
    buttonsToShow() {
        const prefix = `${this.props.rankMode[this.props.eventType]}.`
        let show = []
        for (let tuple of this.props.available) {
            if (tuple[0].startsWith(prefix)) show.push(tuple)
        }

        return show.sort((a, b) => compareDatasetKey(a[0], b[0]))
    }

    setAllToValue(v) {
        let newMap = {...this.props.displayTiers[this.props.eventType]}

        const prefix = `${this.props.rankMode[this.props.eventType]}.`
        for (let [key] of this.props.available) {
            if (key.startsWith(prefix)) newMap[key] = v
        }

        requestStoragePermission("saint-settings").then(() => {
            this.props.replaceVisFlags(this.props.eventType, newMap)
        })
    }

    toggleSingle(k) {
        requestStoragePermission("saint-settings").then(() => {
            this.props.toggleVisSet(this.props.eventType, k)
        })   
    }

    render() {
        const map = this.props.displayTiers[this.props.eventType]

        return <div className="row">
            <div className="col-md-4">
                <div className="card kars-event-cutoff-card">
                    <div className="card-body">
                        <button className="btn btn-sm btn-primary mr-3"
                            onClick={() => this.setAllToValue(true)}>Show All</button>          
                        <button className="btn btn-sm btn-secondary"
                            onClick={() => this.setAllToValue(false)}>Clear All</button>
                    </div>
                </div>
            </div>

            {this.buttonsToShow().map((tuple) => {
                const [k, label] = tuple
                return <div className="col-md-4" key={k}>
                    <div className="card kars-event-cutoff-card" 
                        onClick={() => this.toggleSingle(k)}>
                        <div className="card-body">
                            <p className="card-text h6">
                                {label} {" "}
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
    replaceVisFlags: (m, p) => dispatch({
        type: `${SaintUserConfig.actions.replaceVisFlags}`,
        forType: m,
        newMap: p
    }),
    toggleVisSet: (m, k) => dispatch({
        type: `${SaintUserConfig.actions.toggleVisFlag}`,
        forType: m,
        key: k
    })
}})(_SaintDisplayEditor)

class _SaintGraphRangeController extends MultiValueSwitch {
    getChoices() {
        return [9999, 168, 72, 24, 12]
    }

    getCurrentSelection() {
        return this.props.timeScale
    }

    getLabelForChoice(v) {
        if (v == 9999) {
            return Infra.strings.Saint.GraphPeriod.All
        }

        if (v > 24) {
            return Infra.strings.formatString(Infra.strings.Saint.GraphPeriod.Days, v / 24)
        }

        return Infra.strings.formatString(Infra.strings.Saint.GraphPeriod.Hours, v)
    }

    changeValue(v) {
        requestStoragePermission("saint-settings").then(() => {
            this.props.setTimeScale(v)
        })
    }
}
const SaintGraphRangeController = connect((state) => { return {
    timeScale: state.saint.timeScale
}}, (dispatch) => { return {
    setTimeScale: (s) => dispatch({type: `${SaintUserConfig.actions.setTimeScale}`, scale: s})
}})(_SaintGraphRangeController)

const SaintRoot = connect(
    (state) => { return {editMode: state.saint.editMode} },
    (dispatch) => { return {
        enterEditMode: () => dispatch({
            type: `${SaintUserConfig.actions.enterEditMode}`
        })
    }}
)(
    function(props) {
        const pad2 = (n) => n < 10? "0" + n : n
        const checkin = `${pad2(props.lastCheckin.getHours())}:${pad2(props.lastCheckin.getMinutes())}`
        const update = `${pad2(props.lastUpdate.getHours())}:${pad2(props.lastUpdate.getMinutes())}`

        return <div>
            <h2 className="h4 mb-2">
                {Infra.strings.Saint.HeaderCurrentTiers}
                <button className="btn btn-sm btn-primary ml-3"
                    onClick={() => props.enterEditMode()}>{props.editMode? 
                        Infra.strings.Saint.ExitEditMode :
                        Infra.strings.Saint.EnterEditMode}</button>
            </h2>
            <div className="kars-sub-navbar is-left">
                <span className="item">{Infra.strings.Saint.RankTypeSwitchLabel}</span>
                <SaintRankTypeSelector eventType={props.eventType} />
            </div>
            {props.editMode?
                <SaintDisplayEditor eventType={props.eventType} available={props.availableSet}/> :
                <SaintDisplayBoard eventType={props.eventType} summaryData={props.summaries} 
                    trackType={props.trackType} /> }
            <p className="small mb-3 mt-3">
                {props.timerInstalled? Infra.strings.Saint.UpdateTimeNote : Infra.strings.Saint.UpdatesDisabled}
                {" "}
                {Infra.strings.formatString(Infra.strings.Saint.UpdateTime, checkin, update)}
            </p>
            <div className="kars-sub-navbar is-left">
                <span className="item">{Infra.strings.Saint.GraphPeriodLabel}</span>
                <SaintGraphRangeController />
            </div>
        </div>
    }
)

class SaintDisplayController {
    constructor(canvas) {
        this.canvas = canvas
        this.eventType = canvas.dataset.eventType

        if (canvas.dataset.trackWorld == "top10") {
            this.chartData = new SaintT10DatasetCoordinator(canvas.dataset.serverId, 
                parseInt(canvas.dataset.eventId))
            this.eventType = canvas.dataset.eventType + "_t10"
        } else {
            this.chartData = new SaintDatasetCoordinator(canvas.dataset.serverId, 
                parseInt(canvas.dataset.eventId))
        }
        
        this.trackType = canvas.dataset.trackWorld
        this.chart = null
        this.timeout = null
        this.firstTime = true

        this.eventStart = Date.parse(canvas.dataset.rangeStart)
        this.eventEnd = Date.parse(canvas.dataset.rangeEnd)

        Infra.store.dispatch({type: `${SaintUserConfig.actions.loadFromLocalStorage}`})
        Infra.store.subscribe(() => {
            if (Infra.canWritebackState() && hasStoragePermission()) {
                const {displayTiers, rankMode, timeScale} = Infra.store.getState().saint
                localStorage.setItem("as$$saint", JSON.stringify({displayTiers, rankMode, timeScale}))
            }
            this.chartData.moreBacklog().then(() => {
                this.updateReact()
                if (this.chart) {
                    this.recolor()
                    this.updateChart(false, true)
                }
            })
        })
    }

    install() {
        this.installTimer()
        this.updateReact()
    }

    installTimer() {
        const tfunc = () => {
            this.refreshData()
            if (Date.now() >= this.eventEnd) {
                console.debug("Event ended - disabling updates.")
                this.disableUpdates()
            }
        }

        const now = new Date()
        const then = new Date(now)
        const min = now.getMinutes()
        if (min < 15) {
            then.setMinutes(15)
        } else if (min < 30) {
            then.setMinutes(30)
        } else if (min < 45) {
            then.setMinutes(45)
        } else {
            then.setHours(then.getHours() + 1)
            then.setMinutes(0)
        }

        this.timeout = setTimeout(() => {
            tfunc()
            this.timeout = setInterval(tfunc, 15 * 60 * 1000)
        }, then.getTime() - now.getTime())
    }

    installChart() {
        const ctarget = document.querySelector("#saint-graph-target").getContext("2d")
        this.chart = new Chart.Chart(ctarget, {
            type: "line",
            data: {
                datasets: []
            },
            options: {
                _saintAppearance: null,
                animation: {duration: 0},
                hover: {animationDuration: 0},
                responsiveAnimationDuration: 0,
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        ticks: {beginAtZero: true, fontColor: THEME_VARS.dark.textColor, mirror: false},
                        gridLines: {
                            color: THEME_VARS.dark.gridLines,
                            zeroLineColor: THEME_VARS.dark.gridLines
                        }
                    }],
                    xAxes: [{
                        type: "time",
                        ticks: {source: "auto", fontColor: THEME_VARS.dark.textColor, maxRotation: 0, min: new Date()},
                        gridLines: {
                            color: THEME_VARS.dark.gridLines,
                            zeroLineColor: THEME_VARS.dark.gridLines
                        }
                    }]
                },
                legend: {
                    labels: {fontColor: THEME_VARS.dark.textColor}
                }
            }
        })

        this.recolor()
        this.updateChart()
        console.log(this.chart)
    }

    recolor() {
        const appearance = effectiveAppearance()
        // fuck this shit
        if (this.chart && this.chart.config.options._saintAppearance != appearance) {
            this.chart.config.options.scales.yAxes[0].ticks.fontColor = THEME_VARS[appearance].textColor
            this.chart.config.options.scales.xAxes[0].ticks.fontColor = THEME_VARS[appearance].textColor
            this.chart.config.options.scales.yAxes[0].gridLines.color = THEME_VARS[appearance].gridLines
            this.chart.config.options.scales.xAxes[0].gridLines.color = THEME_VARS[appearance].gridLines
            this.chart.config.options.scales.yAxes[0].gridLines.zeroLineColor = THEME_VARS[appearance].gridLines
            this.chart.config.options.scales.xAxes[0].gridLines.zeroLineColor = THEME_VARS[appearance].gridLines
            this.chart.config.options.legend.labels.fontColor = THEME_VARS[appearance].textColor
            this.chart.config.options._saintAppearance = appearance
            this.chart.update()
        }
    }

    disableUpdates() {
        if (this.timeout) {
            clearInterval(this.timeout)
            this.timeout = null
        }
    }

    refreshData() {
        this.chartData.refresh().then(() => {
            console.log(this.chartData)
            this.updateReact()
            if (this.chart) {
                this.updateChart()
            }

            if (this.firstTime) {
                this.firstTime = false
                this.refreshData()
            }
        })
    }

    // eslint-disable-next-line no-unused-vars
    updateChart(_allowAnimation = true, force = false) {
        const state = Infra.store.getState().saint

        const prefix = `${state.rankMode[this.eventType]}.`
        const vset = Object.keys(state.displayTiers[this.eventType]).filter((v) => {
            return v.startsWith(prefix) && state.displayTiers[this.eventType][v]
        })
        vset.sort(compareDatasetKey)
        
        const current = this.chart.config.data.datasets.map((v) => v.key)

        if (!arraySame(vset, current) || force) {
            let i = 0
            let datasets = []
            for (let key of vset) {
                if (!this.chartData.datasets[key]) {
                    continue
                }

                datasets.push({
                    key,
                    label: this.chartData.localizeDatasetName(key),
                    fill: false,
                    borderColor: COLOURS[i % COLOURS.length]((i / COLOURS.length) | 0),
                    ...this.chartData.datasets[key]
                })
                ++i
            }

            this.chart.config.data.datasets = datasets
        }

        // Update the constraints...
        const scale = this.chartData.calcBounds(state.timeScale)
        this.chart.config.options.scales.xAxes[0].ticks.min = scale.min
        this.chart.config.options.scales.xAxes[0].ticks.max = scale.max

        this.chart.update()
    }

    updateReact() {
        const set = Object.keys(this.chartData.datasets).sort()
        const summaries = this.chartData.summaryForDatasets(set)
        ReactDOM.render(<Provider store={Infra.store}>
            <SaintRoot 
                availableSet={set.map((s) => [s, summaries[s].label])}
                eventType={this.eventType}
                summaries={summaries}
                lastCheckin={new Date(this.chartData.lastCheckinTime * 1000)}
                lastUpdate={new Date(this.chartData.lastUpdateTime * 1000)}
                timerInstalled={this.timeout !== null}
                trackType={this.trackType} />
        </Provider>, this.canvas)
    }
}
  
let controller

export function injectIntoPage() {
    Infra.store.injectReducers({saint: SaintUserConfig.reducer})
    const tgt = document.getElementById("saint-inject-target")
    controller = new SaintDisplayController(tgt)
    controller.install()
    controller.refreshData()
    controller.installChart()
}