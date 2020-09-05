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

function injectStatsExpandersForMainCardPage() {
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

function doGalleryExpandForRoot(root) {
    const state = root.classList.toggle("folded")
    const icon = root.querySelector(".t-expand-indicator")
    if (state) {
        icon.classList.remove("ion-ios-arrow-down")
        icon.classList.add("ion-ios-arrow-forward")
    } else {
        icon.classList.remove("ion-ios-arrow-forward")
        icon.classList.add("ion-ios-arrow-down")
    }
}

function injectStatsExpandersForGallery() {
    const actionSingle = (event) => {
        const a = event.target
        let root = a
        while (root && !root.hasAttribute("data-expand-target")) {
            root = root.parentNode
        }

        if (!root) {
            return
        }

        doGalleryExpandForRoot(root)
    }

    const actionAll = (event) => {
        const a = event.target
        let root = a
        while (root && !root.hasAttribute("data-expand-group-root")) {
            root = root.parentNode
        }
        if (!root) {
            return
        }
        const groupContents = root.querySelectorAll("[data-expand-target]")
        for (let i = 0; i < groupContents.length; i++) {
            doGalleryExpandForRoot(groupContents[i])
        }
    }

    const nodeList = document.querySelectorAll(".t-expand-click-target")
    for (let i = 0; i < nodeList.length; ++i) {
        const a = nodeList[i]
        a.addEventListener("click", actionSingle, false)
    }
    console.debug(`Album: injected ${nodeList.length} gallery card expanders.`)

    const gbList = document.querySelectorAll(".t-expand-group-target")
    for (let i = 0; i < gbList.length; ++i) {
        const a = gbList[i]
        a.addEventListener("click", actionAll, false)
    }
}

export function injectIntoPage() {
    injectStatsExpandersForMainCardPage()
    injectStatsExpandersForGallery()
}
