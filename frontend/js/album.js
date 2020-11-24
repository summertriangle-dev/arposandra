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

async function displayMemberList(forMemberId, targetNode) {
    const iconList = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.onreadystatechange = () => {
            if (xhr.readyState !== 4) return
    
            if (xhr.status == 200) {
                const json = JSON.parse(xhr.responseText)
                resolve(json.result)
            } else {
                reject()
            }
        }
        xhr.open("GET", `/api/private/member_icon_list/${forMemberId}.json`)
        xhr.send()
    })

    const container = document.createElement("div")
    container.className = targetNode.className
    iconList.forEach((v) => {
        const a = document.createElement("a")
        a.className = "card-icon"
        a.href = `/card/${v[0]}`
        const img = document.createElement("img")
        img.src = v[1]
        img.width = img.height = 64

        a.appendChild(img)
        container.appendChild(a)
    })

    const parent = targetNode.parentNode
    parent.insertBefore(container, targetNode)
    parent.removeChild(targetNode)
}

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

function injectMemberListExpanders() {
    const action = (event) => {
        event.preventDefault()
        const a = event.currentTarget
        if (a.dataset.inFlight) {
            return
        }

        a.dataset.inFlight = true
        a.textContent = "..."
        const expandForId = parseInt(a.dataset.memberId)
        const fillTarget = a.parentNode
        displayMemberList(expandForId, fillTarget).catch((error) => {
            console.error("While loading member icon list:", error)
            a.classList.add("btn-danger")
            delete a.dataset.inFlight
            a.textContent = "Error"
        })
    }

    const nodeList = document.querySelectorAll("[data-memlist-expander]")
    for (let i = 0; i < nodeList.length; ++i) {
        const a = nodeList[i]
        a.addEventListener("click", action, false)
    }
    console.debug(`Album: injected ${nodeList.length} memlist expanders.`)
}

export function injectIntoPage() {
    injectStatsExpandersForMainCardPage()
    injectStatsExpandersForGallery()
    injectMemberListExpanders()
}
