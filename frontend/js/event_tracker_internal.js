import Infra from "./infra"
import {createSlice} from "@reduxjs/toolkit"

const DEFAULT_DATASETS_TO_SHOW_MARATHON = {
    "points.1000": true,
    "points.10000": true,
    "points.20000": true,
    "points.50000": true,
}

const DEFAULT_DATASETS_TO_SHOW_MINING = {
    "points.1000": true,
    "points.10000": true,
    "points.20000": true,
    "points.50000": true,
    "voltage.1000": true,
    "voltage.5000": true,
    "voltage.10000": true,
}

// slow!
export function compareDatasetKey(a, b) {
    const A = parseInt(a.split(".")[1])
    const B = parseInt(b.split(".")[1])
    return A - B
}

export function rankTypesForEventType(eventType) {
    switch(eventType) {
    case "mining":
        return ["points", "voltage"]
    default:
        return ["points"]
    }
}

export function toRankTypeFriendlyName(key) {
    switch(key) {
    case "voltage": return Infra.strings.Saint.DatasetFriendlyName.Voltage 
    case "points": return Infra.strings.Saint.DatasetFriendlyName.Points
    default: return key
    }
}

export function localizeDatasetName(dsn) {
    let s = dsn.split(".")
    if (s.length !== 2) return s

    let criteria = toRankTypeFriendlyName(s[0])    

    return Infra.strings.formatString(Infra.strings.Saint.DatasetNameFormat, s[1], criteria)
}

export const SaintUserConfig = createSlice({
    name: "saint",
    initialState: {
        displayTiers: {
            marathon: DEFAULT_DATASETS_TO_SHOW_MARATHON, 
            mining: DEFAULT_DATASETS_TO_SHOW_MINING
        },
        rankMode: {
            marathon: "points",
            mining: "points",
        },
        timeScale: 24
    },
    reducers: {
        setMode: (state, action) => {
            state.rankMode[action.forType] = action.mode
        },
        toggleVisFlag: (state, action) => {
            state.displayTiers[action.forType][action.key] = !state.displayTiers[action.forType][action.key]
        },
        replaceVisFlags: (state, action) => {
            state.displayTiers[action.forType] = action.newMap
        },
        setTimeScale: (state, action) => {
            state.timeScale = parseInt(action.scale)
        },
        enterEditMode: (state) => {
            if (!state.editMode)
                state.editMode = true
            else
                state.editMode = false
        },
        loadFromLocalStorage: (state) => {
            const ls = localStorage.getItem("as$$saint")
            if (!ls) {
                return
            }

            const json = JSON.parse(ls)
            if (json.rankMode) {
                Object.assign(state.rankMode, json.rankMode)
            }
            if (json.displayTiers && json.displayTiers.length === undefined) {
                state.displayTiers = json.displayTiers
            }
            if (json.timeScale) {
                state.timeScale = parseInt(json.timeScale)
            }
        }
    }
})

export class SaintDatasetCoordinator {
    constructor(serverid, eventID) {
        this.serverid = serverid
        this.eventId = eventID
        this.lastUpdateTime = 0
        this.lastCheckinTime = 0
        this.status = 0
        this.lastError = null
        this.backlogStatus = 0
        this.inFlight = 0

        this.datasets = {}
    }

    async refresh(hard = false) {
        if (hard) {
            this.lastUpdateTime = 0
        }

        if (this.inFlight) {
            console.warn("Dataset coordinator was asked to refresh with a request already in flight!")
            return
        }

        const api = await this.getUpdateFromAPI(this.lastUpdateTime,
            Infra.store.getState().saint.timeScale)

        if (!api.result) {
            this.status = 0
            this.lastError = api.error? api.error : "Unknown server error"
            return
        }

        const datasets = api.result.datasets
        if (api.result.is_new) {
            this.datasets = {}
            this.backlogStatus = Infra.store.getState().saint.timeScale
        }

        let maxT = -1
        for (let name of Object.keys(datasets)) {
            const rawDS = datasets[name]
            if (Object.hasOwnProperty.call(this.datasets, name)) {
                this.datasets[name].data.push(...SaintDatasetCoordinator.reshapeDataset(rawDS))
            } else {
                this.datasets[name] = {
                    name: localizeDatasetName(name),
                    data: SaintDatasetCoordinator.reshapeDataset(rawDS),
                    rankType: name.split(".")[0],
                }
            }

            if (rawDS.length > 0) {
                const t = rawDS[rawDS.length - 1][0]
                if (t > maxT) {
                    maxT = t
                }
            }
        }

        if (maxT > 0) {
            this.lastUpdateTime = maxT
        }
    }

    async moreBacklog() {
        if (this.backlogStatus < Infra.store.getState().saint.timeScale) {
            return await this.refresh(true)
        }
        console.debug("Doing nothing, we have enough past data")
    }

    static reshapeDataset(dso) {
        return dso.map((v) => {return {x: new Date(v[0] * 1000), y: v[1]}})
    }

    summaryForDatasets(wantNames) {
        let ret = {}
        for (let key of wantNames) {
            if (!Object.hasOwnProperty.call(this.datasets, key)) {
                continue
            }

            const len = this.datasets[key].data.length
            ret[key] = {
                points: this.datasets[key].data[len - 1].y,
                label: this.datasets[key].name
            }

            if (len > 1) {
                ret[key].delta = ret[key].points - this.datasets[key].data[len - 2].y
            }

            if (len > 2) {
                ret[key].delta2 = ret[key].delta - (this.datasets[key].data[len - 2].y 
                    - this.datasets[key].data[len - 3].y)
            }
        }
        return ret
    }

    getUpdateURL() {
        return `/api/private/saint/${this.serverid}/${this.eventId}/tiers.json`
    }

    async getUpdateFromAPI(last, timeScale) {
        this.inFlight = true

        const xhr = new XMLHttpRequest()
        return new Promise((resolve, reject) => {
            xhr.onreadystatechange = () => {
                if (xhr.readyState !== 4) return
                this.inFlight = false
    
                if (xhr.status == 200) {
                    const json = JSON.parse(xhr.responseText)
                    if (!json.error) {
                        this.lastCheckinTime = (Date.now() / 1000) | 0
                    }
                    resolve(json)
                } else {
                    reject()
                }
            }

            let query = "?"
            if (last) {
                query += `after=${Math.ceil(last)}`
            } else {
                query += `back=${timeScale}`
            }
            xhr.open("GET", this.getUpdateURL() + query)
            xhr.send()
        })
    }

    calcBounds(numHours) {
        let max
        const k = Object.keys(this.datasets)
        if (k.length < 1) {
            max = null
        } else {
            max = Math.max(...k.map((v) => this.datasets[v].data[this.datasets[v].data.length - 1].x.getTime()))
        }

        if (numHours === 9999 || !max) {
            return {min: null, max}
        }

        let minDate = new Date(max)
        minDate.setHours(minDate.getHours() - numHours)

        const realMin = Math.min(...k.map((v) => this.datasets[v].data[0].x.getTime()))
        if (minDate.getTime() < realMin) {
            minDate = new Date(realMin)
        }

        return {min: minDate, max}
    }
}

class SaintTop10DatasetCoordinator extends SaintDatasetCoordinator {
    getUpdateURL() {
        return `/api/private/saint/${this.serverid}/${this.eventId}/top10.json`
    }
}
