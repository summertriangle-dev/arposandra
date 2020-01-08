import { createSlice } from "@reduxjs/toolkit"

export const AlbumStore = createSlice({
    name: "album",
    initialState: {
        ttInfluence: {},
        cardLevel: {}
    },
    reducers: {
        setCardTTInfluence: (state, action) => {
            state.ttInfluence[action.cid] = action.influence
        },
        setCardLevel: (state, action) => {
            let prev = state.cardLevel[action.cid]
            if (!prev) {
                prev = {level: action.level, limitBreak: 0}
            } else {
                prev.level = action.level
            }
            state.cardLevel[action.cid] = prev
        },
        setCardLimitBreak: (state, action) => {
            let prev = state.cardLevel[action.cid]
            if (!prev) {
                prev = {level: 1, limitBreak: action.limitBreak}
            } else {
                prev.limitBreak = action.limitBreak
            }
            state.cardLevel[action.cid] = prev
        },
        loadFromLocalStorage: (state, action) => {
            const p = action.payload || {}
            return {ttInfluence: p.ttInfluence || {}, cardLevel: p.cardLevel || {}}
        }
    }
})

export function injectIntoPage() {
    const action = (event) => {
        const a = event.target
        document.querySelector(`.kars-card-base-stats[data-cid="${a.dataset.cmidTarget}"]`)
            .classList.add("kars-stats-displaying-extraneous")
    }

    const nodeList = document.querySelectorAll(".kars-show-full-stat-table")
    for (let i = 0; i < nodeList.length; ++i) {
        const a = nodeList[i]
        a.href = "javascript:;"
        a.addEventListener("click", action, false)
    }

    console.debug(`Album: injected ${nodeList.length} stats expanders.`)
}
