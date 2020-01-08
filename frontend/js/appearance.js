import { createSlice } from "@reduxjs/toolkit"
import Infra from "./infra"

function valueIn(it, choices, def) {
    if (choices.indexOf(it) === -1) {
        return def
    }
    return it
}

export const Appearance = createSlice({
    name: "appearance",
    initialState: {
        theme: "system",
        cardDisplayMode: "normal"
    },
    reducers: {
        setTheme: (state, action) => {
            state.theme = action.payload
        },
        setCardDisplayMode: (state, action) => {
            state.cardDisplayMode = action.payload
        },
        loadFromLocalStorage: (state, action) => {
            const p = action.payload || {}
            return {theme: valueIn(p.theme,
                ["system", "light", "dark"], "system"),
            cardDisplayMode: valueIn(p.cardDisplayMode,
                ["normal", "esports", "gallery"], "normal")}
        }
    }
})

let DM_CSS_REGISTRY = {}
let DM_HAS_INITIALIZED_REGISTRY = false
let DM_CURRENT_THEME = "system"

function dmInitThemeRegistry() {
    if (DM_HAS_INITIALIZED_REGISTRY) {
        return
    }

    const themeSheets = document.querySelectorAll("link.theme")
    themeSheets.forEach((sheet) => {
        DM_CSS_REGISTRY[sheet.dataset.appearance] = {css: sheet.href, bg: sheet.dataset.bgColor}
    })
    DM_HAS_INITIALIZED_REGISTRY = true
}

function dmSetAppearance(appearanceStore, initial) {
    if (!Object.hasOwnProperty.call(DM_CSS_REGISTRY, appearanceStore.theme)
        || appearanceStore.theme === DM_CURRENT_THEME) {
        return
    }

    const name = appearanceStore.theme
    const href = DM_CSS_REGISTRY[name].css
    const bg = DM_CSS_REGISTRY[name].bg
    const themeSheets = document.querySelectorAll("link.theme")

    if (initial) {
        const style = `html { background-color: ${bg}; }`
        const fakecss = document.createElement("style")
        fakecss.textContent = style
        themeSheets[0].parentNode.insertBefore(fakecss, themeSheets[0])
        setTimeout(() => fakecss.parentNode.removeChild(fakecss), 250)
    }
    
    const node = document.createElement("link")
    node.href = href
    node.rel = "stylesheet"
    node.className = "theme"
    
    const last = themeSheets[themeSheets.length - 1]
    last.parentNode.insertBefore(node, last)

    for (var i = 0; i < themeSheets.length; i++) {
        const css = themeSheets[i]
        css.parentNode.removeChild(css)
    }

    DM_CURRENT_THEME = name
}

function dmToggleAppearance() {
    const theme = Infra.store.getState().appearance.theme
    let nextAppearance

    if (theme === "system") {
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            nextAppearance = "light"
        } else {
            nextAppearance = "dark"
        }
    } else {
        nextAppearance = theme === "dark"? "light" : "dark"
    }

    Infra.store.dispatch({type: `${Appearance.actions.setTheme}`, payload: nextAppearance})
}

export function initWithRedux(store) {
    dmInitThemeRegistry()

    store.subscribe(() => {
        const state = store.getState().appearance
        console.debug("Appearance: did change...")
        console.debug(`The theme is ${state.theme}. The CDM is ${state.cardDisplayMode}.`)
        dmSetAppearance(state, true)
        document.body.className = `kars-${state.cardDisplayMode}-config`

        if (Infra.canWritebackState()) {
            localStorage.setItem("as$$appearance", JSON.stringify(state))
        }
    })

    const sers = JSON.parse(localStorage.getItem("as$$appearance"))
    if (sers !== undefined) {
        store.dispatch({type: `${Appearance.actions.loadFromLocalStorage}`, payload: sers})
    }

    document.querySelector("#bind-appearance-toggle")
        .addEventListener("click", dmToggleAppearance, false)
}
