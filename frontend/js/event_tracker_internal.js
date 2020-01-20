import Infra from "./infra"
import {createSlice} from "@reduxjs/toolkit"

const DEFAULT_DATASETS_TO_SHOW = [
    "points.50000",
    "points.40000",
    "points.10000",
    "points.1000"
]

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

function localizeDatasetName(dsn) {
    let s = dsn.split(".")
    if (s.length !== 2) return s

    let criteria = toRankTypeFriendlyName(s[0])    

    return Infra.strings.formatString(Infra.strings.Saint.DatasetNameFormat, s[1], criteria)
}

export const SaintUserConfig = createSlice({
    name: "saint",
    initialState: {
        displayTiers: DEFAULT_DATASETS_TO_SHOW,
        rankMode: {
            marathon: "points",
            mining: "points",
        }
    },
    reducers: {
        setMode: (state, action) => {
            state.rankMode[action.forType] = action.mode
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
            if (json.displayTiers && json.displayTiers.length !== undefined) {
                state.displayTiers = displayTiers
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

        this.datasets = {}
    }

    async refresh(hard = false) {
        if (hard) {
            this.lastUpdateTime = 0
        }

        const api = await this.getUpdateFromAPI(this.lastUpdateTime)

        if (!api.result) {
            this.status = 0
            this.lastError = api.error? api.error : "Unknown server error"
            return
        }

        const datasets = api.result.datasets
        if (api.result.is_new) {
            this.datasets = {}
        }

        let maxT = -1
        for (let name of Object.keys(datasets)) {
            const rawDS = datasets[name]
            if (Object.hasOwnProperty.call(this.datasets, name)) {
                this.datasets[name].push(...SaintDatasetCoordinator.reshapeDataset(rawDS))
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
            ret[key] = {points: this.datasets[key].data[len - 1].y}

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

    async getUpdateFromAPI(last) {
        const xhr = new XMLHttpRequest()
        return new Promise((resolve, reject) => {
            xhr.onreadystatechange = () => {
                if (xhr.readyState !== 4) return
    
                if (xhr.status == 200) {
                    const json = JSON.parse(xhr.responseText)
                    if (!json.error) {
                        this.lastCheckinTime = (Date.now() / 1000) | 0
                    }

                    console.debug("Resolving now")
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
